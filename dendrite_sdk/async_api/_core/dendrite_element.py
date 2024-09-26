from __future__ import annotations
import asyncio
import base64
import functools
import time
from typing import TYPE_CHECKING, Optional

from loguru import logger
from playwright.async_api import Locator

from dendrite_sdk.async_api._api.browser_api_client import BrowserAPIClient
from dendrite_sdk.async_api._exceptions.dendrite_exception import IncorrectOutcomeError

if TYPE_CHECKING:
    from dendrite_sdk.async_api._core._base_browser import BaseAsyncDendrite
from dendrite_sdk.async_api._core.models.page_diff_information import (
    PageDiffInformation,
)
from dendrite_sdk.async_api._core._type_spec import Interaction
from dendrite_sdk.async_api._api.response.interaction_response import (
    InteractionResponse,
)
from dendrite_sdk.async_api._api.dto.make_interaction_dto import MakeInteractionDTO


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

            logger.info(
                f'Performing action "{interaction_type}" | element: d_id:"{self.dendrite_id}" {self.locator}'
            )

            if not expected_outcome:
                await func(self, *args, **kwargs)
                return InteractionResponse(status="success", message="")

            api_config = self._dendrite_browser.api_config

            page_before = await self._dendrite_browser.get_active_page()
            page_before_info = await page_before.get_page_information()

            # Call the original method here
            await func(
                self,
                expected_outcome=expected_outcome,
                *args,
                **kwargs,
            )

            await self._wait_for_page_changes(page_before.url)

            page_after = await self._dendrite_browser.get_active_page()
            page_after_info = await page_after.get_page_information()
            page_delta_information = PageDiffInformation(
                page_before=page_before_info, page_after=page_after_info
            )

            dto = MakeInteractionDTO(
                url=page_before.url,
                dendrite_id=self.dendrite_id,
                interaction_type=interaction_type,
                expected_outcome=expected_outcome,
                page_delta_information=page_delta_information,
                api_config=api_config,
            )
            res = await self._browser_api_client.make_interaction(dto)

            if res.status == "failed":
                raise IncorrectOutcomeError(
                    message=res.message,
                    screenshot_base64=page_delta_information.page_after.screenshot_base64,
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
        dendrite_browser: BaseAsyncDendrite,
        browser_api_client: BrowserAPIClient,
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
        self, expected_outcome: Optional[str] = None, *args, **kwargs
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

        try:
            await self.locator.click(timeout=timeout, force=force, *args, **kwargs)
        except Exception as e:
            try:
                await self.locator.click(timeout=2000, force=True, *args, **kwargs)
            except Exception as e:
                await self.locator.dispatch_event("click", timeout=2000)

        return InteractionResponse(status="success", message="")

    @perform_action("fill")
    async def fill(
        self, value: str, expected_outcome: Optional[str] = None, *args, **kwargs
    ) -> InteractionResponse:
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
