from __future__ import annotations

import asyncio
import base64
import functools
import time
from typing import TYPE_CHECKING, Optional

from loguru import logger
from playwright.async_api import Locator

from dendrite.browser._common._exceptions.dendrite_exception import (
    IncorrectOutcomeError,
)
from dendrite.logic import AsyncLogicEngine

if TYPE_CHECKING:
    from .dendrite_browser import AsyncDendrite

from dendrite.models.dto.make_interaction_dto import VerifyActionDTO
from dendrite.models.response.interaction_response import InteractionResponse

from .manager.navigation_tracker import NavigationTracker
from .types import Interaction


def perform_action(interaction_type: Interaction):
    """
    Decorator for performing actions on DendriteElements.

    This decorator wraps methods of AsyncElement to handle interactions,
    expected outcomes, and error handling.

    Args:
        interaction_type (Interaction): The type of interaction being performed.

    Returns:
        function: The decorated function.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(
            self: AsyncElement,
            *args,
            **kwargs,
        ) -> InteractionResponse:
            expected_outcome: Optional[str] = kwargs.pop("expected_outcome", None)

            if not expected_outcome:
                await func(self, *args, **kwargs)
                return InteractionResponse(status="success", message="")

            page_before = await self._dendrite_browser.get_active_page()
            page_before_info = await page_before.get_page_information()
            soup = await page_before._get_previous_soup()
            screenshot_before = page_before_info.screenshot_base64
            tag_name = soup.find(attrs={"d-id": self.dendrite_id})
            # Call the original method here
            await func(
                self,
                expected_outcome=expected_outcome,
                *args,
                **kwargs,
            )

            await self._wait_for_page_changes(page_before.url)

            page_after = await self._dendrite_browser.get_active_page()
            screenshot_after = (
                await page_after.screenshot_manager.take_full_page_screenshot()
            )

            dto = VerifyActionDTO(
                url=page_before.url,
                dendrite_id=self.dendrite_id,
                interaction_type=interaction_type,
                expected_outcome=expected_outcome,
                screenshot_before=screenshot_before,
                screenshot_after=screenshot_after,
                tag_name=str(tag_name),
            )
            res = await self._browser_api_client.verify_action(dto)

            if res.status == "failed":
                raise IncorrectOutcomeError(
                    message=res.message, screenshot_base64=screenshot_after
                )

            return res

        return wrapper

    return decorator


class AsyncElement:
    """
    Represents an element in the Dendrite browser environment. Wraps a Playwright Locator.

    This class provides methods for interacting with and manipulating
    elements in the browser.
    """

    def __init__(
        self,
        dendrite_id: str,
        locator: Locator,
        dendrite_browser: AsyncDendrite,
        browser_api_client: AsyncLogicEngine,
    ):
        """
        Initialize a AsyncElement.

        Args:
            dendrite_id (str): The dendrite_id identifier for this element.
            locator (Locator): The Playwright locator for this element.
            dendrite_browser (AsyncDendrite): The browser instance.
        """
        self.dendrite_id = dendrite_id
        self.locator = locator
        self._dendrite_browser = dendrite_browser
        self._browser_api_client = browser_api_client

    async def outer_html(self):
        return await self.locator.evaluate("(element) => element.outerHTML")

    async def screenshot(self) -> str:
        """
        Take a screenshot of the element and return it as a base64-encoded string.

        Returns:
            str: A base64-encoded string of the JPEG image.
                 Returns an empty string if the screenshot fails.
        """
        image_data = await self.locator.screenshot(type="jpeg", timeout=20000)

        if image_data is None:
            return ""

        return base64.b64encode(image_data).decode()

    @perform_action("click")
    async def click(
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

        page = await self._dendrite_browser.get_active_page()
        navigation_tracker = NavigationTracker(page)
        navigation_tracker.start_nav_tracking()

        try:
            await self.locator.click(timeout=timeout, force=force, *args, **kwargs)
        except Exception as e:
            try:
                await self.locator.click(timeout=2000, force=True, *args, **kwargs)
            except Exception as e:
                await self.locator.dispatch_event("click", timeout=2000)

        if wait_for_navigation:
            has_navigated = await navigation_tracker.has_navigated_since_start()
            if has_navigated:
                try:
                    start_time = time.time()
                    await page.playwright_page.wait_for_load_state("load", timeout=2000)
                    wait_duration = time.time() - start_time
                    # print(f"Waited {wait_duration:.2f} seconds for load state")
                except Exception as e:
                    pass
                    # print(f"Page navigated but failed to wait for load state: {e}")

        return InteractionResponse(status="success", message="")

    @perform_action("fill")
    async def fill(
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
            # First, try to fill the element directly
            await self.locator.fill(value, timeout=timeout, *args, **kwargs)
        except Exception as e:
            # If direct fill fails, try to find a fillable child element
            fillable_child = self.locator.locator(
                'input, textarea, [contenteditable="true"]'
            ).first
            await fillable_child.fill(value, timeout=timeout, *args, **kwargs)

        return InteractionResponse(status="success", message="")

    @perform_action("hover")
    async def hover(
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
        await self.locator.hover(timeout=timeout, *args, **kwargs)

        return InteractionResponse(status="success", message="")

    async def focus(self):
        """
        Focus on the element.
        """
        await self.locator.focus()

    async def highlight(self):
        """
        Highlights the element. This is a convenience method for debugging purposes.
        """
        await self.locator.highlight()

    async def _wait_for_page_changes(self, old_url: str, timeout: float = 2000):
        """
        Wait for page changes after an action.

        Args:
            old_url (str): The URL before the action.
            timeout (float): The maximum time (in milliseconds) to wait for changes.

        Returns:
            bool: True if the page changed, False otherwise.
        """
        # Convert the timeout from milliseconds to seconds
        timeout_in_seconds = timeout / 1000
        start_time = time.time()

        while time.time() - start_time <= timeout_in_seconds:
            page = await self._dendrite_browser.get_active_page()
            if page.url != old_url:
                return True
            await asyncio.sleep(0.1)  # Wait briefly before checking again

        return False
