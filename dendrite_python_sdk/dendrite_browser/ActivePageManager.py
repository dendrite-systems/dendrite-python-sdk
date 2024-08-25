from typing import TYPE_CHECKING, Optional

from loguru import logger
from playwright.async_api import BrowserContext, Page, Frame, Download, FileChooser
from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage


class ActivePageManager:
    def __init__(self, dendrite_browser, browser_context: BrowserContext):
        self.active_page: Optional[DendritePage] = None
        self.browser_context = browser_context
        self.dendrite_browser = dendrite_browser

        browser_context.on("page", self.page_on_open_handler)

    async def get_active_page(self) -> DendritePage:
        if self.active_page == None:
            return await self.open_new_page()

        return self.active_page

    async def page_on_close_handler(self, page):
        agent_soup_page = DendritePage(page, self.dendrite_browser)
        if self.browser_context:
            try:
                if self.active_page and agent_soup_page == self.active_page:
                    await self.active_page.page.title()
            except:
                print("The active tab was closed. Will switch to the last page.")
                if self.browser_context.pages:
                    self.active_page = DendritePage(
                        self.browser_context.pages[-1], self.dendrite_browser
                    )
                    await self.active_page.page.bring_to_front()
                    print("Switched the active tab to: ", self.active_page.url)
                else:
                    await self.open_new_page()
                    print("Opened a new page since all others are closed.")

    async def open_new_page(self) -> DendritePage:
        new_page = await self.browser_context.new_page()
        dendrite_page = DendritePage(new_page, self.dendrite_browser)
        self.active_page = dendrite_page
        return dendrite_page

    async def file_chooser_handler(self, file_chooser: FileChooser):
        if self.active_page:
            logger.debug("Setting file chooser")
            self.active_page._set_file_chooser(file_chooser)

    async def download_handler(self, download: Download):
        if self.active_page:
            self.active_page._set_download(download)

    def page_on_navigation_handler(self, frame: Frame):
        if self.active_page:
            self.active_page.page = frame.page

    def page_on_crash_handler(self, page):
        print("Page crashed:", page.url)
        print("Try to reload")
        page.reload()

    def page_on_open_handler(self, page: Page):
        # page.on("framenavigated", self.page_on_navigation_handler)
        page.on("close", self.page_on_close_handler)
        page.on("crash", self.page_on_crash_handler)
        page.on("filechooser", self.file_chooser_handler)
        page.on("download", self.download_handler)
        self.active_page = DendritePage(page, self.dendrite_browser)
