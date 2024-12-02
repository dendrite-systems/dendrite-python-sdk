from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dendrite.browser.sync_api._core.dendrite_browser import Dendrite
from playwright.sync_api import Browser, Download, Playwright
from dendrite.browser.sync_api._core._impl_browser import ImplBrowser
from dendrite.browser.sync_api._core._type_spec import PlaywrightPage


class LocalImpl(ImplBrowser):

    def __init__(self) -> None:
        pass

    def start_browser(self, playwright: Playwright, pw_options) -> Browser:
        return playwright.chromium.launch(**pw_options)

    def get_download(
        self, dendrite_browser: "Dendrite", pw_page: PlaywrightPage, timeout: float
    ) -> Download:
        return dendrite_browser._download_handler.get_data(pw_page, timeout)

    def configure_context(self, browser: "Dendrite"):
        pass

    def stop_session(self):
        pass
