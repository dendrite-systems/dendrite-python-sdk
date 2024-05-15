import logging
from typing import Any
from uuid import uuid4

from playwright.async_api import async_playwright, Playwright, BrowserContext
from dendrite_python_sdk.dendrite_browser.ActivePageManager import ActivePageManager
from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage
from dendrite_python_sdk.models.LLMConfig import LLMConfig

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

    async def goto(self, url: str) -> DendritePage:
        if self.active_page_manager == None:
            raise Exception("Browser not launched.")

        active_page = await self.active_page_manager.get_active_page()
        await active_page.page.goto(url)
        return await self.active_page_manager.get_active_page()

    def _is_launched(self):
        return self.browser_context != None

    async def launch(self):
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
