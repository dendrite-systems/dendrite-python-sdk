from typing import Optional, TYPE_CHECKING
from loguru import logger
from playwright.sync_api import BrowserContext, Download, FileChooser

if TYPE_CHECKING:
    from dendrite_sdk.sync_api._core.dendrite_browser import Dendrite
from dendrite_sdk.sync_api._core._type_spec import PlaywrightPage
from dendrite_sdk.sync_api._core.dendrite_page import Page


class PageManager:

    def __init__(self, dendrite_browser, browser_context: BrowserContext):
        self.pages: list[Page] = []
        self.active_page: Optional[Page] = None
        self.browser_context = browser_context
        self.dendrite_browser: Dendrite = dendrite_browser
        browser_context.on("page", self._page_on_open_handler)

    def new_page(self) -> Page:
        new_page = self.browser_context.new_page()
        if self.active_page and new_page == self.active_page.playwright_page:
            return self.active_page
        client = self.dendrite_browser._get_browser_api_client()
        dendrite_page = Page(new_page, self.dendrite_browser, client)
        self.pages.append(dendrite_page)
        self.active_page = dendrite_page
        return dendrite_page

    def get_active_page(self) -> Page:
        if self.active_page is None:
            return self.new_page()
        return self.active_page

    def _page_on_close_handler(self, page: PlaywrightPage):
        if self.browser_context and (not self.dendrite_browser.closed):
            copy_pages = self.pages.copy()
            for dendrite_page in copy_pages:
                if dendrite_page.playwright_page == page:
                    self.pages.remove(dendrite_page)
                    break
            if self.pages:
                self.active_page = self.pages[-1]
                self.active_page.playwright_page.bring_to_front()
                logger.debug("Switched the active tab to: ", self.active_page.url)
            else:
                pass

    def _page_on_crash_handler(self, page: PlaywrightPage):
        logger.error(f"Page crashed: {page.url}")
        page.reload()

    def _page_on_download_handler(self, download: Download):
        logger.debug(f"Download started: {download.url}")
        self.dendrite_browser._download_handler.set_event(download)

    def _page_on_filechooser_handler(self, file_chooser: FileChooser):
        logger.debug("File chooser opened")
        self.dendrite_browser._upload_handler.set_event(file_chooser)

    def _page_on_open_handler(self, page: PlaywrightPage):
        page.on("close", self._page_on_close_handler)
        page.on("crash", self._page_on_crash_handler)
        page.on("download", self._page_on_download_handler)
        page.on("filechooser", self._page_on_filechooser_handler)
        client = self.dendrite_browser._get_browser_api_client()
        dendrite_page = Page(page, self.dendrite_browser, client)
        self.pages.append(dendrite_page)
        self.active_page = dendrite_page
