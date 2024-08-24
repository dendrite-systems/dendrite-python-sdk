from __future__ import annotations
import asyncio
import functools
import time

from loguru import logger
from playwright.async_api import Locator

from typing import TYPE_CHECKING, Literal, Optional, Type

from dendrite_python_sdk.exceptions.IncorrectOutcomeException import (
    IncorrectOutcomeException,
)


if TYPE_CHECKING:
    from dendrite_python_sdk.dendrite_browser.DendriteBrowser import DendriteBrowser

from dendrite_python_sdk.dto.MakeInteractionDTO import MakeInteractionDTO
from dendrite_python_sdk.models.PageDeltaInformation import PageDeltaInformation
from dendrite_python_sdk.responses.InteractionResponse import InteractionResponse


class Interaction:
    type: Literal["click", "fill", "hover"]


class ExpectedOutcomeHolder:
    def __init__(self, value: str):
        self.value = value


class Click(Interaction):
    type = "click"


class Fill(Interaction):
    type = "fill"


class Hover(Interaction):
    type = "hover"


def perform_action(interaction_type: Type[Interaction]):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(
            self: DendriteElement,
            *args,
            **kwargs,
        ) -> InteractionResponse:
            expected_outcome = kwargs.pop("expected_outcome", None)

            logger.debug(f"Performing action outcome: {expected_outcome}")

            llm_config = self.dendrite_browser.get_llm_config()

            page_before = await self.dendrite_browser.get_active_page()
            page_before_info = await page_before.get_page_information()

            # Call the original method here
            await func(
                self,
                expected_outcome=expected_outcome,
                *args,
                **kwargs,
            )

            await self.wait_for_page_changes(page_before.url)

            page_after = await self.dendrite_browser.get_active_page()
            page_after_info = await page_after.get_page_information()
            page_delta_information = PageDeltaInformation(
                page_before=page_before_info, page_after=page_after_info
            )

            dto = MakeInteractionDTO(
                url=page_before.url,
                dendrite_id=self.dendrite_id,
                interaction_type="fill",
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
    def __init__(
        self, dendrite_id: str, locator: Locator, dendrite_browser: DendriteBrowser
    ):
        self.dendrite_id = dendrite_id
        self.locator = locator
        self.dendrite_browser = dendrite_browser
        self.browser_api_client = dendrite_browser.browser_api_client

    def get_playwright_locator(self) -> Locator:
        return self.locator

    async def wait_for_page_changes(self, old_url: str, timeout: float = 2):
        start_time = time.time()
        while time.time() - start_time <= timeout:
            page = await self.dendrite_browser.get_active_page()
            if page.url != old_url:
                return True
            await asyncio.sleep(0.1)
        return False

    async def outer_html(self):
        return await self.locator.evaluate("(element) => element.outerHTML")

    @perform_action(Click)
    async def click(
        self, expected_outcome: Optional[str] = None, *args, **kwargs
    ) -> InteractionResponse:  # type: ignore
        timeout = kwargs.pop("timeout", 2000)
        force = kwargs.pop("force", False)

        try:
            await self.locator.click(timeout=timeout, force=force, *args, **kwargs)
        except Exception as e:
            try:
                await self.locator.click(timeout=2000, force=True, *args, **kwargs)
            except Exception as e:
                await self.locator.dispatch_event("click", timeout=2000)

    @perform_action(Fill)
    async def fill(
        self, value: str, expected_outcome: Optional[str] = None, *args, **kwargs
    ) -> InteractionResponse:  # type: ignore

        timeout = kwargs.pop("timeout", 2000)
        await self.locator.fill(value, timeout=timeout, *args, **kwargs)

    @perform_action(Hover)
    async def hover(
        self, expected_outcome: Optional[str] = None, *args, **kwargs
    ) -> InteractionResponse:  # type: ignore

        timeout = kwargs.pop("timeout", 2000)
        await self.locator.hover(timeout=timeout, *args, **kwargs)

    async def highlight(self, *args, **kwargs):
        await self.locator.highlight(*args, **kwargs)
