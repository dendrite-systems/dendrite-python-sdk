import json
from typing import TYPE_CHECKING, Optional
from dendrite.browser._common._exceptions.dendrite_exception import BrowserNotLaunchedError
from dendrite.browser.sync_api._core._impl_browser import ImplBrowser
from dendrite.browser.sync_api._core._type_spec import PlaywrightPage
from dendrite.browser.remote.browserless_config import BrowserlessConfig

if TYPE_CHECKING:
    from dendrite.browser.sync_api._core.dendrite_browser import Dendrite
from dendrite.browser.sync_api._ext_impl.browserbase._client import BrowserbaseClient
from playwright.sync_api import Playwright
from loguru import logger
import urllib.parse
from dendrite.browser.sync_api._ext_impl.browserbase._download import BrowserbaseDownload


class BrowserlessImpl(ImplBrowser):

    def __init__(self, settings: BrowserlessConfig) -> None:
        self.settings = settings
        self._session_id: Optional[str] = None

    def stop_session(self):
        pass

    def start_browser(self, playwright: Playwright, pw_options: dict):
        logger.debug("Starting browser")
        url = self._format_connection_url(pw_options)
        logger.debug(f"Connecting to browser at {url}")
        return playwright.chromium.connect_over_cdp(url)

    def _format_connection_url(self, pw_options: dict) -> str:
        url = self.settings.url.rstrip("?").rstrip("/")
        query = {
            "token": self.settings.api_key,
            "blockAds": self.settings.block_ads,
            "launch": json.dumps(pw_options),
        }
        if self.settings.proxy:
            query["proxy"] = (self.settings.proxy,)
            query["proxyCountry"] = (self.settings.proxy_country,)
        return f"{url}?{urllib.parse.urlencode(query)}"

    def configure_context(self, browser: "Dendrite"):
        pass

    def get_download(
        self,
        dendrite_browser: "Dendrite",
        pw_page: PlaywrightPage,
        timeout: float = 30000,
    ) -> BrowserbaseDownload:
        raise NotImplementedError("Downloads are not supported for Browserless")
