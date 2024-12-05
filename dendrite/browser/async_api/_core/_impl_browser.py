from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Union, overload
from typing_extensions import Literal

if TYPE_CHECKING:
    from dendrite.browser.async_api._core.dendrite_browser import AsyncDendrite

from playwright.async_api import (
    Browser,
    Download,
    Playwright,
    BrowserContext,
    StorageState,
)

from dendrite.browser.async_api._core._type_spec import PlaywrightPage


class ImplBrowser(ABC):
    @abstractmethod
    def __init__(self, settings):
        pass
        # self.settings = settings

    @abstractmethod
    async def get_download(
        self, dendrite_browser: "AsyncDendrite", pw_page: PlaywrightPage, timeout: float
    ) -> Download:
        """
        Retrieves the download event from the browser.

        Returns:
            Download: The download event.

        Raises:
            Exception: If there is an issue retrieving the download event.
        """

    @abstractmethod
    async def start_browser(
        self,
        playwright: Playwright,
        pw_options: dict,
    ) -> Browser:
        """
        Starts the browser session.

        Args:
            playwright: The playwright instance
            pw_options: Playwright launch options

        Returns:
            Browser: A Browser instance
        """

    @abstractmethod
    async def configure_context(self, browser: "AsyncDendrite") -> None:
        """
        Configures the browser context.

        Args:
            browser (AsyncDendrite): The browser to configure.

        Raises:
            Exception: If there is an issue configuring the browser context.
        """

    @abstractmethod
    async def stop_session(self) -> None:
        """
        Stops the browser session.

        Raises:
            Exception: If there is an issue stopping the browser session.
        """
