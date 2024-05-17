from __future__ import annotations
import asyncio
import os
import time

from playwright.async_api import Locator

from typing import TYPE_CHECKING

from dendrite_python_sdk.exceptions.DendriteException import DendriteException
from dendrite_python_sdk.exceptions.IncorrectOutcomeException import (
    IncorrectOutcomeException,
)

if TYPE_CHECKING:
    from dendrite_python_sdk import DendriteBrowser

from dendrite_python_sdk.dto.MakeInteractionDTO import MakeInteractionDTO
from dendrite_python_sdk.models.PageDeltaInformation import PageDeltaInformation
from dendrite_python_sdk.request_handler import make_interaction
from dendrite_python_sdk.responses.InteractionResponse import InteractionResponse


class DendriteLocator:
    def __init__(
        self, dendrite_id: str, locator: Locator, dendrite_browser: DendriteBrowser
    ):
        self.dendrite_id = dendrite_id
        self.locator = locator
        self.dendrite_browser = dendrite_browser

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

    async def click(self, expected_outcome="", *args, **kwargs) -> InteractionResponse:
        llm_config = self.dendrite_browser.get_llm_config()

        page_before = await self.dendrite_browser.get_active_page()
        page_before_info = await page_before.get_page_information()

        timeout = kwargs.pop("timeout", 2000)
        force = kwargs.pop("force", False)

        try:
            await self.locator.click(timeout=timeout, force=force, *args, **kwargs)
        except Exception as e:
            try:
                await self.locator.click(timeout=2000, force=True, *args, **kwargs)
            except Exception as e:
                await self.locator.dispatch_event("click", timeout=2000)

        await self.wait_for_page_changes(page_before.url)

        page_after = await self.dendrite_browser.get_active_page()
        await page_after.get_playwright_page().wait_for_load_state("load")
        page_after_info = await page_after.get_page_information()

        e = DendriteException(
            message="", screenshot_base64=page_before_info.screenshot_base64
        )
        e.store_exception_screenshot(
            os.path.join(os.getcwd(), "exceptions"), name="before"
        )

        e = DendriteException(
            message="", screenshot_base64=page_after_info.screenshot_base64
        )
        e.store_exception_screenshot(
            os.path.join(os.getcwd(), "exceptions"), name="after"
        )

        page_delta_information = PageDeltaInformation(
            page_before=page_before_info, page_after=page_after_info
        )

        print("page_after_info: ", page_after_info.url)

        dto = MakeInteractionDTO(
            url=page_before.url,
            dendrite_id=self.dendrite_id,
            interaction_type="click",
            expected_outcome=expected_outcome,
            page_delta_information=page_delta_information,
            llm_config=llm_config,
        )
        res = await make_interaction(dto)

        if res.status == "failed":
            raise IncorrectOutcomeException(
                message=res.message,
                screenshot_base64=page_delta_information.page_after.screenshot_base64,
            )

        return res

    async def fill(self, value: str, expected_outcome="", *args, **kwargs):
        if expected_outcome == "":
            expected_outcome = (
                f"That the text '{value}' is filled into the targeted element."
            )

        llm_config = self.dendrite_browser.get_llm_config()

        page_before = await self.dendrite_browser.get_active_page()
        page_before_info = await page_before.get_page_information()

        timeout = kwargs.pop("timeout", 2000)
        await self.locator.fill(value, timeout=timeout, *args, **kwargs)

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
        res = await make_interaction(dto)
        return res
