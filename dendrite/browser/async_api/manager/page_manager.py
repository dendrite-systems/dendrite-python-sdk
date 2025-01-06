from typing import TYPE_CHECKING, Optional

from loguru import logger
from playwright.async_api import BrowserContext, Download, FileChooser

if TYPE_CHECKING:
    from ..dendrite_browser import AsyncDendrite

from ..dendrite_page import AsyncPage
from ..types import PlaywrightPage


class PageManager:
    def __init__(self, dendrite_browser, browser_context: BrowserContext):
        self.pages: list[AsyncPage] = []
        self.active_page: Optional[AsyncPage] = None
        self.browser_context = browser_context
        self.dendrite_browser: AsyncDendrite = dendrite_browser

        # Handle existing pages in the context
        existing_pages = browser_context.pages
        if existing_pages:
            for page in existing_pages:
                client = self.dendrite_browser.logic_engine
                dendrite_page = AsyncPage(page, self.dendrite_browser, client)
                self.pages.append(dendrite_page)
                # Set the first existing page as active
                if self.active_page is None:
                    self.active_page = dendrite_page

        browser_context.on("page", self._page_on_open_handler)

    async def new_page(self) -> AsyncPage:
        new_page = await self.browser_context.new_page()

        # if we added the page via the new_page method, we don't want to add it again since it is done in the on_open_handler
        if self.active_page and new_page == self.active_page.playwright_page:
            return self.active_page

        client = self.dendrite_browser.logic_engine
        dendrite_page = AsyncPage(new_page, self.dendrite_browser, client)
        self.pages.append(dendrite_page)
        self.active_page = dendrite_page
        return dendrite_page

    async def get_active_page(self) -> AsyncPage:
        if self.active_page is None:
            return await self.new_page()

        return self.active_page

    async def _page_on_close_handler(self, page: PlaywrightPage):
        if self.browser_context and not self.dendrite_browser.closed:
            copy_pages = self.pages.copy()
            is_active_page = False
            for dendrite_page in copy_pages:
                if dendrite_page.playwright_page == page:
                    self.pages.remove(dendrite_page)
                    if dendrite_page == self.active_page:
                        is_active_page = True
                    break

            for i in reversed(range(len(self.pages))):
                try:
                    self.active_page = self.pages[i]
                    await self.pages[i].playwright_page.bring_to_front()
                    break
                except Exception as e:
                    logger.warning(f"Error switching to the next page: {e}")
                    continue

    async def _page_on_crash_handler(self, page: PlaywrightPage):
        logger.error(f"Page crashed: {page.url}")
        await page.reload()

    async def _page_on_download_handler(self, download: Download):
        logger.debug(f"Download started: {download.url}")
        self.dendrite_browser._download_handler.set_event(download)

    async def _page_on_filechooser_handler(self, file_chooser: FileChooser):
        logger.debug("File chooser opened")
        self.dendrite_browser._upload_handler.set_event(file_chooser)

    def _page_on_open_handler(self, page: PlaywrightPage):
        page.on("close", self._page_on_close_handler)
        page.on("crash", self._page_on_crash_handler)
        page.on("download", self._page_on_download_handler)
        page.on("filechooser", self._page_on_filechooser_handler)

        client = self.dendrite_browser.logic_engine
        dendrite_page = AsyncPage(page, self.dendrite_browser, client)
        self.pages.append(dendrite_page)
        self.active_page = dendrite_page
