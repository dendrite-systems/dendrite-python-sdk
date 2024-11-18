from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dendrite.browser.async_api._core.dendrite_browser import AsyncDendrite

from dendrite.browser.async_api._core._type_spec import PlaywrightPage
from playwright.async_api import Download, Browser, Playwright


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
    async def configure_context(self, browser: "AsyncDendrite") -> None:
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