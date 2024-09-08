import os
from typing import Optional
from loguru import logger
from playwright.async_api import Playwright, Locator
from dendrite_sdk._core.dendrite_remote_browser import DendriteRemoteBrowser
from dendrite_sdk.ext._remote_provider import RemoteProvider
from dendrite_sdk.ext.browserbase._download import BrowserbaseDownload
from ._client import BrowserbaseClient


class BrowserbaseProvider(RemoteProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        enable_proxy: bool = False,
        enable_downloads=False,
    ) -> None:
        super().__init__()

        _api_key = (
            api_key if api_key is not None else os.environ.get("BROWSERBASE_API_KEY")
        )
        _project_id = (
            project_id
            if project_id is not None
            else os.environ.get("BROWSERBASE_PROJECT_ID")
        )

        if not _api_key:
            raise ValueError("BROWSERBASE_API_KEY environment variable is not set")
        if not _project_id:
            raise ValueError("BROWSERBASE_PROJECT_ID environment variable is not set")

        self._client = BrowserbaseClient(_api_key, _project_id)
        self._enable_proxy = enable_proxy
        self._enable_downloads = enable_downloads
        self._managed_session = enable_downloads  # This is a flag to determine if the session is managed by us or not
        self._session_id: Optional[str] = None

    async def _close(self, DendriteRemoteBrowser):
        if self._session_id:
            await self._client.stop_session(self._session_id)

    async def _start_browser(self, playwright: Playwright):
        logger.debug("Starting browser")
        if self._managed_session:
            self._session_id = await self._client.create_session()
        url = await self._client.connect_url(self._enable_proxy, self._session_id)
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

    async def get_download(
        self, dendrite_browser: DendriteRemoteBrowser, timeout
    ) -> BrowserbaseDownload:
        if not self._session_id:
            raise ValueError(
                "Downloads are not enabled for this provider. Specify enable_downloads=True in the constructor"
            )
        download = await dendrite_browser._download_handler.get_data(timeout)
        await self._client.save_downloads_on_disk(
            self._session_id, await download.path(), 30
        )
        return BrowserbaseDownload(self._session_id, download, self._client)
