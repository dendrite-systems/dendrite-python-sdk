from __future__ import annotations
import asyncio
import functools
import time
from typing import TYPE_CHECKING, Optional

from playwright.async_api import Locator

if TYPE_CHECKING:
    from dendrite_python_sdk._core.dendrite_browser import DendriteBrowser
from dendrite_python_sdk._core.models.page_diff_information import PageDiffInformation
from dendrite_python_sdk._core._type_spec import Interaction
from dendrite_python_sdk._api.response.interaction_response import InteractionResponse
from dendrite_python_sdk._api.dto.make_interaction_dto import MakeInteractionDTO
from dendrite_python_sdk._exceptions.incorrect_outcome_exception import (
    IncorrectOutcomeException,
)


def perform_action(interaction_type: Interaction):
    """
    Decorator for performing actions on DendriteElements.

    This decorator wraps methods of DendriteElement to handle interactions,
    expected outcomes, and error handling.

    Args:
        interaction_type (Interaction): The type of interaction being performed.

    Returns:
        function: The decorated function.
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(
            self: DendriteElement,
            *args,
            **kwargs,
        ) -> InteractionResponse:
            expected_outcome: str | None = kwargs.pop("expected_outcome", None)

            if not expected_outcome:
                return await func(self, *args, **kwargs)

            llm_config = self.dendrite_browser.llm_config

            page_before = await self.dendrite_browser.get_active_page()
            page_before_info = await page_before._get_page_information()

            # Call the original method here
            await func(
                self,
                expected_outcome=expected_outcome,
                *args,
                **kwargs,
            )

            await self._wait_for_page_changes(page_before.url)

            page_after = await self.dendrite_browser.get_active_page()
            page_after_info = await page_after._get_page_information()
            page_delta_information = PageDiffInformation(
                page_before=page_before_info, page_after=page_after_info
            )

            dto = MakeInteractionDTO(
                url=page_before.url,
                dendrite_id=self.dendrite_id,
                interaction_type=interaction_type,
                expected_outcome=expected_outcome,
                page_delta_information=page_delta_information,
                llm_config=llm_config,
            )
            res = await self.browser_api_client.make_interaction(dto)

            if res.status == "failed":
                raise IncorrectOutcomeException(
                    message=res.message,
                    screenshot_base64=page_delta_information.page_after.screenshot_base64,
                )

            return res

        return wrapper

    return decorator


class DendriteElement:
    """
    Represents an element in the Dendrite browser environment. Wraps a Playwright Locator.

    This class provides methods for interacting with and manipulating
    elements in the browser.
    """

    def __init__(
        self, dendrite_id: str, locator: Locator, dendrite_browser: DendriteBrowser
    ):
        """
        Initialize a DendriteElement.

        Args:
            dendrite_id (str): The dendrite_id identifier for this element.
            locator (Locator): The Playwright locator for this element.
            dendrite_browser (DendriteBrowser): The browser instance.
        """
        self.dendrite_id = dendrite_id
        self.locator = locator
        self.dendrite_browser = dendrite_browser
        self.browser_api_client = dendrite_browser._browser_api_client

    async def outer_html(self):
        return await self.locator.evaluate("(element) => element.outerHTML")

    @perform_action("click")
    async def click(
        self, expected_outcome: Optional[str] = None, *args, **kwargs
    ) -> InteractionResponse:  # type: ignore
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

        try:
            await self.locator.click(timeout=timeout, force=force, *args, **kwargs)
        except Exception as e:
            try:
                await self.locator.click(timeout=2000, force=True, *args, **kwargs)
            except Exception as e:
                await self.locator.dispatch_event("click", timeout=2000)

    @perform_action("fill")
    async def fill(
        self, value: str, expected_outcome: Optional[str] = None, *args, **kwargs
    ) -> InteractionResponse:  # type: ignore
        """
        Fill the element with a value. If an expected outcome is provided, the LLM will be used to verify the outcome and raise an exception if the outcome is not as expected.
        All additional arguments are passed to the Playwright fill method.

        Args:
            value (str): The value to fill the element with.
            expected_outcome (Optional[str]): The expected outcome of the fill action.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            InteractionResponse: The response from the interaction.
        """

        timeout = kwargs.pop("timeout", 2000)
        await self.locator.fill(value, timeout=timeout, *args, **kwargs)

    @perform_action("hover")
    async def hover(
        self, expected_outcome: Optional[str] = None, *args, **kwargs
    ) -> InteractionResponse:  # type: ignore
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

    async def highlight(self):
        """
        Highlights the element. This is a convenience method for debugging purposes.
        """
        await self.locator.highlight()

    async def _wait_for_page_changes(self, old_url: str, timeout: float = 2):
        """
        Wait for page changes after an action.

        Args:
            old_url (str): The URL before the action.
            timeout (float): The maximum time to wait for changes.

        Returns:
            bool: True if the page changed, False otherwise.
        """
        start_time = time.time()
        while time.time() - start_time <= timeout:
            page = await self.dendrite_browser.get_active_page()
            if page.url != old_url:
                return True
            await asyncio.sleep(0.1)
        return False
