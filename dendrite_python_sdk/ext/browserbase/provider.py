import os
from typing import Optional
from loguru import logger
from playwright.async_api import Playwright, Locator
from dendrite_python_sdk._core.dendrite_remote_browser import DendriteRemoteBrowser
from dendrite_python_sdk.ext._remote_provider import RemoteProvider
from dendrite_python_sdk.ext._browser_base.download import BrowserBaseDownload
from ._client import create_session, stop_session

Locator.set_input_files


class BrowserBaseProvider(RemoteProvider[BrowserBaseDownload]):
    def __init__(
        self,
        api_key: Optional[str] = None,
        enable_proxy: bool = False,
        enable_downloads=False,
    ) -> None:
        super().__init__()
        self._api_key = (
            api_key if api_key is not None else os.environ.get("BROWSERBASE_API_KEY")
        )
        if not self._api_key:
            raise ValueError("BROWSERBASE_API_KEY environment variable is not set")

        self._enable_proxy = enable_proxy
        self._enable_downloads = enable_downloads
        self._managed_session = enable_downloads  # This is a flag to determine if the session is managed by us or not
        self._session_id: Optional[str] = None

    async def _close(self, DendriteRemoteBrowser):
        if self._session_id:
            await stop_session(self._session_id)

    async def _start_browser(self, playwright: Playwright):
        logger.debug("Starting browser")
        if self._managed_session:
            self._session_id = await create_session()
        url = await self.browser_ws_url(self._session_id)
        logger.debug(f"Connecting to browser at {url}")
        return await playwright.chromium.connect_over_cdp(url)

    async def configure_context(self, browser: DendriteRemoteBrowser):
        logger.debug("Configuring browser context")

        page = await browser.get_active_page()
        pw_page = page.playwright_page
        client = await browser.browser_context.new_cdp_session(pw_page)  # type: ignore
        await client.send(
            "Browser.setDownloadBehavior",
            {
                "behavior": "allow",
                "downloadPath": "downloads",
                "eventsEnabled": True,
            },
        )

    async def browser_ws_url(self, session_id: Optional[str] = None) -> str:
        url = f"wss://connect.browserbase.com?apiKey={self._api_key}"
        if session_id:
            url += f"&sessionId={session_id}"
        if self._enable_proxy:
            url += "&enableProxy=true"
        return url

    async def get_download(
        self, dendrite_browser: DendriteRemoteBrowser
    ) -> BrowserBaseDownload:
        if not self._session_id:
            raise ValueError(
                "Downloads are not enabled for this provider. Specify enable_downloads=True in the constructor"
            )
        import browserbase

        download = await dendrite_browser._download_handler.get_data()
        return BrowserBaseDownload(self._session_id, download)
