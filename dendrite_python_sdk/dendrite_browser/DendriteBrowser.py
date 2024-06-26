import logging
from typing import Any, List, Optional, Union
from uuid import uuid4
from urllib.parse import quote
import os

from playwright.async_api import async_playwright, Playwright, BrowserContext
from dendrite_python_sdk.dendrite_browser.ActivePageManager import ActivePageManager
from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage
from dendrite_python_sdk.dto.GoogleSearchDTO import GoogleSearchDTO
from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.request_handler import google_search_request
from dendrite_python_sdk.responses.GoogleSearchResponse import (
    SearchResult,
)
from dendrite_python_sdk.request_handler import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DendriteBrowser:
    def __init__(
        self,
        openai_api_key: str,
        id=None,
        dendrite_api_key: Optional[str] = None,
        playwright_options: Any = {
            "headless": False,
        },
    ):
        self.id = uuid4() if id == None else id
        self.dendrite_api_key = dendrite_api_key
        self.playwright_options = playwright_options
        self.playwright: Optional[Playwright] = None
        self.browser_context: Optional[BrowserContext] = None
        self.active_page_manager: Optional[ActivePageManager] = None

        llm_config = LLMConfig(openai_api_key=openai_api_key)
        self.llm_config = llm_config

        if dendrite_api_key:
            config["dendrite_api_key"] = dendrite_api_key

    async def get_active_page(self) -> DendritePage:
        active_page_manager = await self._get_active_page_manager()
        return await active_page_manager.get_active_page()

    def get_llm_config(self):
        return self.llm_config

    async def goto(
        self, url: str, scroll_through_entire_page: Optional[bool] = True
    ) -> DendritePage:
        active_page_manager = await self._get_active_page_manager()
        active_page = await active_page_manager.get_active_page()
        try:
            await active_page.page.goto(url, timeout=10000)
        except TimeoutError:
            print("Timeout when loading page but continuing anyways.")
        except Exception as e:
            print(f"Timeout when loading page but continuing anyways. {e}")

        if scroll_through_entire_page:
            await active_page.scroll_through_entire_page()

        return await active_page_manager.get_active_page()

    def _is_launched(self):
        return self.browser_context != None

    async def _get_active_page_manager(self) -> ActivePageManager:
        if not self.active_page_manager:
            _, _, active_page_manager = await self.launch()
            return active_page_manager
        else:
            return self.active_page_manager

    async def google_search(
        self,
        query: str,
        filter_results_prompt: Optional[str] = None,
        load_all_results: Optional[bool] = True,
    ) -> List[SearchResult]:
        query = quote(query)
        url = f"https://www.google.com/search?q={query}"
        page = await self.goto(url, scroll_through_entire_page=False)
        page_information = await page.get_page_information()

        if load_all_results == True:
            try:
                reject_all_cookies = await page.get_interactable_element(
                    "The reject all cookies button"
                )
                await reject_all_cookies.get_playwright_locator().click(timeout=0)
            except Exception as e:
                print("Failed to close reject all button")

            await page.scroll_to_bottom()

        dto = GoogleSearchDTO(
            query=query,
            filter_results_prompt=filter_results_prompt,
            page_information=page_information,
            llm_config=self.llm_config,
        )

        response = await google_search_request(dto)
        return response.results

    async def launch(self):
        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"
        self.playwright = await async_playwright().start()
        browser = await self.playwright.chromium.launch(**self.playwright_options)
        self.browser_context = await browser.new_context()
        await self.browser_context.add_init_script(
            path="dendrite_python_sdk/dendrite_browser/scripts/eventListenerPatch.js"
        )
        self.active_page_manager = ActivePageManager(self, self.browser_context)
        return browser, self.browser_context, self.active_page_manager

    async def new_page(self) -> DendritePage:
        active_page_manager = await self._get_active_page_manager()
        return await active_page_manager.open_new_page()

    async def add_cookies(self, cookies):
        if not self.browser_context:
            raise Exception("Browser context not initialized")

        await self.browser_context.add_cookies(cookies)

    async def close(self):
        if self.browser_context:
            await self.browser_context.close()

        if self.playwright:
            await self.playwright.stop()

    async def get_download(self):
        pass
