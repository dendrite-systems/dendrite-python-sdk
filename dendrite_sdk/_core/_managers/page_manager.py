from typing import Optional, TYPE_CHECKING

from loguru import logger
from playwright.async_api import BrowserContext, Page, Download, FileChooser

if TYPE_CHECKING:
    from dendrite_sdk._core._base_browser import BaseDendriteBrowser
from dendrite_sdk._core.dendrite_page import DendritePage


class PageManager:
    def __init__(self, dendrite_browser, browser_context: BrowserContext):
        self.active_page: Optional[DendritePage] = None
        self.browser_context = browser_context
        self.dendrite_browser: BaseDendriteBrowser = dendrite_browser

        browser_context.on("page", self._page_on_open_handler)

    async def new_page(self) -> DendritePage:
        new_page = await self.browser_context.new_page()
        dendrite_page = DendritePage(new_page, self.dendrite_browser)
        self.active_page = dendrite_page
        return dendrite_page

    async def get_active_page(self) -> DendritePage:
        if self.active_page is None:
            return await self.new_page()

        return self.active_page

    async def _page_on_close_handler(self, page: Page):
        agent_soup_page = DendritePage(page, self.dendrite_browser)
        if self.browser_context:
            try:
                if self.active_page and agent_soup_page == self.active_page:
                    await self.active_page.playwright_page.title()
            except:
                logger.debug("The active tab was closed. Will switch to the last page.")
                if self.browser_context.pages:
                    self.active_page = DendritePage(
                        self.browser_context.pages[-1], self.dendrite_browser
                    )
                    await self.active_page.playwright_page.bring_to_front()
                    logger.debug("Switched the active tab to: ", self.active_page.url)
                else:
                    await self.new_page()
                    logger.debug("Opened a new page since all others are closed.")

    async def _file_chooser_handler(self, file_chooser: FileChooser):
        if self.active_page:
            self.dendrite_browser._upload_handler.set_event(file_chooser)

    async def _download_handler(self, download: Download):
        if self.active_page:
            self.dendrite_browser._download_handler.set_event(download)

    async def _page_on_crash_handler(self, page: Page):
        logger.error(f"Page crashed: {page.url}")
        await page.reload()

    def _page_on_open_handler(self, page: Page):
        page.on("close", self._page_on_close_handler)
        page.on("crash", self._page_on_crash_handler)
        page.on("filechooser", self._file_chooser_handler)
        page.on("download", self._download_handler)
        self.active_page = DendritePage(page, self.dendrite_browser)
