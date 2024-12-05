import json
from typing import TYPE_CHECKING, Optional

from dendrite.browser._common._exceptions.dendrite_exception import (
    BrowserNotLaunchedError,
)
from dendrite.browser.async_api.protocol.browser_protocol import BrowserProtocol
from dendrite.browser.async_api.types import PlaywrightPage
from dendrite.browser.remote.browserless_config import BrowserlessConfig

if TYPE_CHECKING:
    from dendrite.browser.async_api.dendrite_browser import AsyncDendrite

import urllib.parse

from loguru import logger
from playwright.async_api import Playwright

from dendrite.browser.async_api.browser_impl.browserbase._client import (
    BrowserbaseClient,
)
from dendrite.browser.async_api.browser_impl.browserbase._download import (
    AsyncBrowserbaseDownload,
)


class BrowserlessImpl(BrowserProtocol):
    def __init__(self, settings: BrowserlessConfig) -> None:
        self.settings = settings
        self._session_id: Optional[str] = None

    async def stop_session(self):
        pass

    async def start_browser(self, playwright: Playwright, pw_options: dict):
        logger.debug("Starting browser")
        url = self._format_connection_url(pw_options)
        logger.debug(f"Connecting to browser at {url}")
        return await playwright.chromium.connect_over_cdp(url)

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

    async def configure_context(self, browser: "AsyncDendrite"):
        pass

    async def get_download(
        self,
        dendrite_browser: "AsyncDendrite",
        pw_page: PlaywrightPage,
        timeout: float = 30000,
    ) -> AsyncBrowserbaseDownload:
        raise NotImplementedError("Downloads are not supported for Browserless")
