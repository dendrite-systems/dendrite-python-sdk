from __future__ import annotations
import time
import base64
import functools
import time
from typing import TYPE_CHECKING, Optional
from loguru import logger
from playwright.sync_api import Locator
from dendrite.browser._common._exceptions.dendrite_exception import (
    IncorrectOutcomeError,
)
from dendrite.logic import LogicEngine

if TYPE_CHECKING:
    from .dendrite_browser import Dendrite
from dendrite.models.dto.make_interaction_dto import VerifyActionDTO
from dendrite.models.response.interaction_response import InteractionResponse
from .manager.navigation_tracker import NavigationTracker
from .types import Interaction


def perform_action(interaction_type: Interaction):
    """
    Decorator for performing actions on DendriteElements.

    This decorator wraps methods of Element to handle interactions,
    expected outcomes, and error handling.

    Args:
        interaction_type (Interaction): The type of interaction being performed.

    Returns:
        function: The decorated function.
    """

    def decorator(func):

        @functools.wraps(func)
        def wrapper(self: Element, *args, **kwargs) -> InteractionResponse:
            expected_outcome: Optional[str] = kwargs.pop("expected_outcome", None)
            if not expected_outcome:
                func(self, *args, **kwargs)
                return InteractionResponse(status="success", message="")
            page_before = self._dendrite_browser.get_active_page()
            page_before_info = page_before.get_page_information()
            soup = page_before._get_previous_soup()
            screenshot_before = page_before_info.screenshot_base64
            tag_name = soup.find(attrs={"d-id": self.dendrite_id})
            func(self, *args, expected_outcome=expected_outcome, **kwargs)
            self._wait_for_page_changes(page_before.url)
            page_after = self._dendrite_browser.get_active_page()
            screenshot_after = page_after.screenshot_manager.take_full_page_screenshot()
            dto = VerifyActionDTO(
                url=page_before.url,
                dendrite_id=self.dendrite_id,
                interaction_type=interaction_type,
                expected_outcome=expected_outcome,
                screenshot_before=screenshot_before,
                screenshot_after=screenshot_after,
                tag_name=str(tag_name),
            )
            res = self._browser_api_client.verify_action(dto)
            if res.status == "failed":
                raise IncorrectOutcomeError(
                    message=res.message, screenshot_base64=screenshot_after
                )
            return res

        return wrapper

    return decorator


class Element:
    """
    Represents an element in the Dendrite browser environment. Wraps a Playwright Locator.

    This class provides methods for interacting with and manipulating
    elements in the browser.
    """

    def __init__(
        self,
        dendrite_id: str,
        locator: Locator,
        dendrite_browser: Dendrite,
        browser_api_client: LogicEngine,
    ):
        """
        Initialize a Element.

        Args:
            dendrite_id (str): The dendrite_id identifier for this element.
            locator (Locator): The Playwright locator for this element.
            dendrite_browser (Dendrite): The browser instance.
        """
        self.dendrite_id = dendrite_id
        self.locator = locator
        self._dendrite_browser = dendrite_browser
        self._browser_api_client = browser_api_client

    def outer_html(self):
        return self.locator.evaluate("(element) => element.outerHTML")

    def screenshot(self) -> str:
        """
        Take a screenshot of the element and return it as a base64-encoded string.

        Returns:
            str: A base64-encoded string of the JPEG image.
                 Returns an empty string if the screenshot fails.
        """
        image_data = self.locator.screenshot(type="jpeg", timeout=20000)
        if image_data is None:
            return ""
        return base64.b64encode(image_data).decode()

    @perform_action("click")
    def click(
        self,
        expected_outcome: Optional[str] = None,
        wait_for_navigation: bool = True,
        *args,
        **kwargs,
    ) -> InteractionResponse:
        """
        Click the element.

        Args:
            expected_outcome (Optional[str]): The expected outcome of the click action.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            InteractionResponse: The response from the interaction.
        """
        timeout = kwargs.pop("timeout", 2000)
        force = kwargs.pop("force", False)
        page = self._dendrite_browser.get_active_page()
        navigation_tracker = NavigationTracker(page)
        navigation_tracker.start_nav_tracking()
        try:
            self.locator.click(*args, timeout=timeout, force=force, **kwargs)
        except Exception as e:
            try:
                self.locator.click(*args, timeout=2000, force=True, **kwargs)
            except Exception as e:
                self.locator.dispatch_event("click", timeout=2000)
        if wait_for_navigation:
            has_navigated = navigation_tracker.has_navigated_since_start()
            if has_navigated:
                try:
                    start_time = time.time()
                    page.playwright_page.wait_for_load_state("load", timeout=2000)
                    wait_duration = time.time() - start_time
                except Exception as e:
                    pass
        return InteractionResponse(status="success", message="")

    @perform_action("fill")
    def fill(
        self, value: str, expected_outcome: Optional[str] = None, *args, **kwargs
    ) -> InteractionResponse:
        """
        Fill the element with a value. If the element itself is not fillable,
        it attempts to find and fill a fillable child element.

        Args:
            value (str): The value to fill the element with.
            expected_outcome (Optional[str]): The expected outcome of the fill action.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            InteractionResponse: The response from the interaction.
        """
        timeout = kwargs.pop("timeout", 2000)
        try:
            self.locator.fill(value, *args, timeout=timeout, **kwargs)
        except Exception as e:
            fillable_child = self.locator.locator(
                'input, textarea, [contenteditable="true"]'
            ).first
            fillable_child.fill(value, *args, timeout=timeout, **kwargs)
        return InteractionResponse(status="success", message="")

    @perform_action("hover")
    def hover(
        self, expected_outcome: Optional[str] = None, *args, **kwargs
    ) -> InteractionResponse:
        """
        Hover over the element.
        All additional arguments are passed to the Playwright fill method.

        Args:
            expected_outcome (Optional[str]): The expected outcome of the hover action.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            InteractionResponse: The response from the interaction.
        """
        timeout = kwargs.pop("timeout", 2000)
        self.locator.hover(*args, timeout=timeout, **kwargs)
        return InteractionResponse(status="success", message="")

    def focus(self):
        """
        Focus on the element.
        """
        self.locator.focus()

    def highlight(self):
        """
        Highlights the element. This is a convenience method for debugging purposes.
        """
        self.locator.highlight()

    def _wait_for_page_changes(self, old_url: str, timeout: float = 2000):
        """
        Wait for page changes after an action.

        Args:
            old_url (str): The URL before the action.
            timeout (float): The maximum time (in milliseconds) to wait for changes.

        Returns:
            bool: True if the page changed, False otherwise.
        """
        timeout_in_seconds = timeout / 1000
        start_time = time.time()
        while time.time() - start_time <= timeout_in_seconds:
            page = self._dendrite_browser.get_active_page()
            if page.url != old_url:
                return True
            time.sleep(0.1)
        return False
