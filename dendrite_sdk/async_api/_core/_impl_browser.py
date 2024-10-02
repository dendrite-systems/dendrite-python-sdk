from abc import ABC, abstractmethod
import os
from typing import Optional

from loguru import logger

from dendrite_sdk._common._exceptions.dendrite_exception import BrowserNotLaunchedError
from dendrite_sdk.async_api._core._base_browser import BaseAsyncDendrite
from dendrite_sdk.async_api._core._impl_mapping import (
    BFloatSettings,
    BrowserBaseSettings,
)
from dendrite_sdk.async_api._core._type_spec import PlaywrightPage
from playwright.async_api import Download, Browser, Playwright

from dendrite_sdk.async_api._core.dendrite_browser import AsyncDendrite
from dendrite_sdk.async_api.ext.browserbase._client import BrowserbaseClient
from dendrite_sdk.async_api.ext.browserbase._download import AsyncBrowserbaseDownload


class ImplBrowser(ABC):
    @abstractmethod
    def __init__(self, settings):
        pass
        # self.settings = settings

    @abstractmethod
    async def get_download(self, pw_page: PlaywrightPage, timeout: float) -> Download:
        """
        Retrieves the download event from the browser.

        Returns:
            Download: The download event.

        Raises:
            Exception: If there is an issue retrieving the download event.
        """
        pass

    @abstractmethod
    async def start_browser(self, playwright: Playwright, pw_options: dict) -> Browser:
        """
        Starts the browser session.

        Returns:
            Browser: The browser session.

        Raises:
            Exception: If there is an issue starting the browser session.
        """
        pass

    @abstractmethod
    async def configure_context(self, browser: BaseAsyncDendrite) -> None:
        """
        Configures the browser context.

        Args:
            browser (AsyncDendrite): The browser to configure.

        Raises:
            Exception: If there is an issue configuring the browser context.
        """
        pass

    @abstractmethod
    async def stop_session(self) -> None:
        """
        Stops the browser session.

        Raises:
            Exception: If there is an issue stopping the browser session.
        """
        pass


class LocalImpl(ImplBrowser):
    def __init__(self, settings: BFloatSettings) -> None:
        self.settings = settings

    async def start_browser(self, playwright: Playwright, pw_options) -> Browser:
        return await playwright.chromium.launch(**pw_options)

    async def get_download(
        self,
        dendrite_browser: BaseAsyncDendrite,
        pw_page: PlaywrightPage,
        timeout: float,
    ) -> Download:
        return await dendrite_browser._download_handler.get_data(pw_page, timeout)

    async def configure_context(self, browser: BaseAsyncDendrite):
        pass

    async def stop_session(self):
        pass


class BrowserBaseImpl(ImplBrowser):
    def __init__(self, settings: BrowserBaseSettings) -> None:
        self.settings = settings
        self._client = BrowserbaseClient(
            self.settings.api_key, self.settings.project_id
        )
        self._session_id: Optional[str] = None

    async def stop_session(self):
        if self._session_id:
            await self._client.stop_session(self._session_id)

    async def _start_browser(self, playwright: Playwright):
        logger.debug("Starting browser")
        self._session_id = await self._client.create_session()
        url = await self._client.connect_url(
            self.settings.enable_proxy, self._session_id
        )
        logger.debug(f"Connecting to browser at {url}")
        return await playwright.chromium.connect_over_cdp(url)

    async def configure_context(self, browser: AsyncDendrite):
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
        dendrite_browser: AsyncDendrite,
        pw_page: PlaywrightPage,
        timeout: float = 30000,
    ) -> AsyncBrowserbaseDownload:
        if not self._session_id:
            raise ValueError(
                "Downloads are not enabled for this provider. Specify enable_downloads=True in the constructor"
            )
        download = await dendrite_browser._download_handler.get_data(pw_page, timeout)
        await self._client.save_downloads_on_disk(
            self._session_id, await download.path(), 30
        )
        return AsyncBrowserbaseDownload(self._session_id, download, self._client)
