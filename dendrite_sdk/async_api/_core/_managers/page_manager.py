from typing import Optional, TYPE_CHECKING

from loguru import logger
from playwright.async_api import BrowserContext, Page, Download, FileChooser

if TYPE_CHECKING:
    from dendrite_sdk.async_api._core._base_browser import BaseAsyncDendrite
from dendrite_sdk.async_api._core.dendrite_page import AsyncPage


class PageManager:
    def __init__(self, dendrite_browser, browser_context: BrowserContext):
        self.pages: list[AsyncPage] = []
        self.active_page: Optional[AsyncPage] = None
        self.browser_context = browser_context
        self.dendrite_browser: BaseAsyncDendrite = dendrite_browser

        browser_context.on("page", self._page_on_open_handler)

    async def new_page(self) -> AsyncPage:
        new_page = await self.browser_context.new_page()

        # if we added the page via the new_page method, we don't want to add it again since it is done in the on_open_handler
        if self.active_page and new_page == self.active_page.playwright_page:
            return self.active_page

        dendrite_page = AsyncPage(new_page, self.dendrite_browser)
        self.pages.append(dendrite_page)
        self.active_page = dendrite_page
        return dendrite_page

    async def get_active_page(self) -> AsyncPage:
        if self.active_page is None:
            return await self.new_page()

        return self.active_page

    async def _page_on_close_handler(self, page: Page):
        if self.browser_context and not self.dendrite_browser.closed:
            copy_pages = self.pages.copy()
            for dendrite_page in copy_pages:
                if dendrite_page.playwright_page == page:
                    self.pages.remove(dendrite_page)
                    break

            if self.pages:
                self.active_page = self.pages[-1]
                await self.active_page.playwright_page.bring_to_front()
                logger.debug("Switched the active tab to: ", self.active_page.url)
            else:
                pass

    async def _page_on_crash_handler(self, page: Page):
        logger.error(f"Page crashed: {page.url}")
        await page.reload()

    def _page_on_open_handler(self, page: Page):
        page.on("close", self._page_on_close_handler)
        page.on("crash", self._page_on_crash_handler)

        dendrite_page = AsyncPage(page, self.dendrite_browser)
        self.pages.append(dendrite_page)
        self.active_page = dendrite_page
