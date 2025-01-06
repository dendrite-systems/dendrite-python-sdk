from typing import TYPE_CHECKING, Optional

from dendrite.browser._common._exceptions.dendrite_exception import (
    BrowserNotLaunchedError,
)
from dendrite.browser.async_api.protocol.browser_protocol import BrowserProtocol
from dendrite.browser.async_api.types import PlaywrightPage
from dendrite.browser.remote.browserbase_config import BrowserbaseConfig

if TYPE_CHECKING:
    from dendrite.browser.async_api.dendrite_browser import AsyncDendrite

from loguru import logger
from playwright.async_api import Playwright

from ._client import BrowserbaseClient
from ._download import AsyncBrowserbaseDownload


class BrowserbaseImpl(BrowserProtocol):
    def __init__(self, settings: BrowserbaseConfig) -> None:
        self.settings = settings
        self._client = BrowserbaseClient(
            self.settings.api_key, self.settings.project_id
        )
        self._session_id: Optional[str] = None

    async def stop_session(self):
        if self._session_id:
            await self._client.stop_session(self._session_id)

    async def start_browser(self, playwright: Playwright, pw_options: dict):
        logger.debug("Starting browser")
        self._session_id = await self._client.create_session()
        url = await self._client.connect_url(
            self.settings.enable_proxy, self._session_id
        )
        logger.debug(f"Connecting to browser at {url}")
        return await playwright.chromium.connect_over_cdp(url)

    async def configure_context(self, browser: "AsyncDendrite"):
        logger.debug("Configuring browser context")

        page = await browser.get_active_page()
        pw_page = page.playwright_page

        if browser.browser_context is None:
            raise BrowserNotLaunchedError()

        client = await browser.browser_context.new_cdp_session(pw_page)
        await client.send(
            "Browser.setDownloadBehavior",
            {
                "behavior": "allow",
                "downloadPath": "downloads",
                "eventsEnabled": True,
            },
        )

    async def get_download(
        self,
        dendrite_browser: "AsyncDendrite",
        pw_page: PlaywrightPage,
        timeout: float = 30000,
    ) -> AsyncBrowserbaseDownload:
        if not self._session_id:
            raise ValueError(
                "Downloads are not enabled for this provider. Specify enable_downloads=True in the constructor"
            )
        logger.debug("Getting download")
        download = await dendrite_browser._download_handler.get_data(pw_page, timeout)
        await self._client.save_downloads_on_disk(
            self._session_id, await download.path(), 30
        )
        return AsyncBrowserbaseDownload(self._session_id, download, self._client)
