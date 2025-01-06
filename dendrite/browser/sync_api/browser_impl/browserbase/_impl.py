from typing import TYPE_CHECKING, Optional
from dendrite.browser._common._exceptions.dendrite_exception import (
    BrowserNotLaunchedError,
)
from dendrite.browser.sync_api.protocol.browser_protocol import BrowserProtocol
from dendrite.browser.sync_api.types import PlaywrightPage
from dendrite.browser.remote.browserbase_config import BrowserbaseConfig

if TYPE_CHECKING:
    from dendrite.browser.sync_api.dendrite_browser import Dendrite
from loguru import logger
from playwright.sync_api import Playwright
from ._client import BrowserbaseClient
from ._download import BrowserbaseDownload


class BrowserbaseImpl(BrowserProtocol):

    def __init__(self, settings: BrowserbaseConfig) -> None:
        self.settings = settings
        self._client = BrowserbaseClient(
            self.settings.api_key, self.settings.project_id
        )
        self._session_id: Optional[str] = None

    def stop_session(self):
        if self._session_id:
            self._client.stop_session(self._session_id)

    def start_browser(self, playwright: Playwright, pw_options: dict):
        logger.debug("Starting browser")
        self._session_id = self._client.create_session()
        url = self._client.connect_url(self.settings.enable_proxy, self._session_id)
        logger.debug(f"Connecting to browser at {url}")
        return playwright.chromium.connect_over_cdp(url)

    def configure_context(self, browser: "Dendrite"):
        logger.debug("Configuring browser context")
        page = browser.get_active_page()
        pw_page = page.playwright_page
        if browser.browser_context is None:
            raise BrowserNotLaunchedError()
        client = browser.browser_context.new_cdp_session(pw_page)
        client.send(
            "Browser.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": "downloads", "eventsEnabled": True},
        )

    def get_download(
        self,
        dendrite_browser: "Dendrite",
        pw_page: PlaywrightPage,
        timeout: float = 30000,
    ) -> BrowserbaseDownload:
        if not self._session_id:
            raise ValueError(
                "Downloads are not enabled for this provider. Specify enable_downloads=True in the constructor"
            )
        logger.debug("Getting download")
        download = dendrite_browser._download_handler.get_data(pw_page, timeout)
        self._client.save_downloads_on_disk(self._session_id, download.path(), 30)
        return BrowserbaseDownload(self._session_id, download, self._client)
