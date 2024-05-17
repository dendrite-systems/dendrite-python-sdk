import logging
from typing import Any, Optional
from uuid import uuid4
from urllib.parse import quote
import os

from playwright.async_api import async_playwright, Playwright, BrowserContext
from dendrite_python_sdk.dendrite_browser.ActivePageManager import ActivePageManager
from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage
from dendrite_python_sdk.dto.GoogleSearchDTO import GoogleSearchDTO
from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.request_handler import google_search_request
from dendrite_python_sdk.responses.GoogleSearchResponse import GoogleSearchResponse

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DendriteBrowser:
    def __init__(
        self,
        llm_config: LLMConfig,
        id=None,
        playwright_options: Any = {"headless": False},
    ):
        self.id = uuid4() if id == None else id
        self.playwright_options = playwright_options
        self.playwright: Playwright | None = None
        self.browser_context: BrowserContext | None = None
        self.active_page_manager: ActivePageManager | None = None
        self.llm_config = llm_config

    async def get_active_page(self) -> DendritePage:
        if self.active_page_manager == None:
            raise Exception("Browser not launched.")

        return await self.active_page_manager.get_active_page()

    def get_llm_config(self):
        return self.llm_config

    async def goto(self, url: str, load_entire_page=True) -> DendritePage:
        if self.active_page_manager == None:
            raise Exception("Browser not launched.")

        active_page = await self.active_page_manager.get_active_page()
        await active_page.page.goto(url)

        if load_entire_page:
            await active_page.load_entire_page()

        return await self.active_page_manager.get_active_page()

    def _is_launched(self):
        return self.browser_context != None

    async def google_search(
        self, query: str, filter_results_prompt: Optional[str] = None
    ) -> GoogleSearchResponse:
        query = quote(query)
        url = f"https://www.google.com/search?q={query}"
        page = await self.goto(url)
        page_information = await page.get_page_information()

        try:
            reject_all_cookies = await page.get_interactable_element(
                "The reject all cookies button"
            )
            await reject_all_cookies.click()
        except Exception as e:
            print("Failed to close reject all button")

        await page.scroll_to_bottom()

        dto = GoogleSearchDTO(
            query=query,
            filter_results_prompt=filter_results_prompt,
            page_information=page_information,
            llm_config=self.llm_config,
        )

        return await google_search_request(dto)

    async def launch(self):
        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"
        self.playwright = await async_playwright().start()
        browser = await self.playwright.chromium.launch(**self.playwright_options)
        self.browser_context = await browser.new_context()
        self.active_page_manager = ActivePageManager(self, self.browser_context)

    async def new_page(self) -> DendritePage:
        if self._is_launched() == False:
            await self.launch()

        if self.active_page_manager:
            return await self.active_page_manager.open_new_page()

        raise Exception("Failed to open new page.")

    async def close(self):
        if self.browser_context:
            await self.browser_context.close()

        if self.playwright:
            await self.playwright.stop()
