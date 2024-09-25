from typing import Optional, TYPE_CHECKING
from loguru import logger
from playwright.sync_api import BrowserContext, Page, Download, FileChooser

if TYPE_CHECKING:
    from dendrite_sdk.sync_api._core._base_browser import BaseDendriteBrowser
from dendrite_sdk.sync_api._core.dendrite_page import DendritePage


class PageManager:

    def __init__(self, dendrite_browser, browser_context: BrowserContext):
        self.pages: list[DendritePage] = []
        self.active_page: Optional[DendritePage] = None
        self.browser_context = browser_context
        self.dendrite_browser: BaseDendriteBrowser = dendrite_browser
        browser_context.on("page", self._page_on_open_handler)

    def new_page(self) -> DendritePage:
        new_page = self.browser_context.new_page()
        if self.active_page and new_page == self.active_page.playwright_page:
            return self.active_page
        dendrite_page = DendritePage(new_page, self.dendrite_browser)
        self.pages.append(dendrite_page)
        self.active_page = dendrite_page
        return dendrite_page

    def get_active_page(self) -> DendritePage:
        if self.active_page is None:
            return self.new_page()
        return self.active_page

    def _page_on_close_handler(self, page: Page):
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

    def _page_on_crash_handler(self, page: Page):
        logger.error(f"Page crashed: {page.url}")
        page.reload()

    def _page_on_open_handler(self, page: Page):
        page.on("close", self._page_on_close_handler)
        page.on("crash", self._page_on_crash_handler)
        dendrite_page = DendritePage(page, self.dendrite_browser)
        self.pages.append(dendrite_page)
        self.active_page = dendrite_page
