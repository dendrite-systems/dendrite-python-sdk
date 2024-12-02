from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dendrite.browser.sync_api._core.dendrite_browser import Dendrite
from playwright.sync_api import Browser, Download, Playwright
from dendrite.browser.sync_api._core._type_spec import PlaywrightPage


class ImplBrowser(ABC):

    @abstractmethod
    def __init__(self, settings):
        pass

    @abstractmethod
    def get_download(
        self, dendrite_browser: "Dendrite", pw_page: PlaywrightPage, timeout: float
    ) -> Download:
        """
        Retrieves the download event from the browser.

        Returns:
            Download: The download event.

        Raises:
            Exception: If there is an issue retrieving the download event.
        """

    @abstractmethod
    def start_browser(self, playwright: Playwright, pw_options: dict) -> Browser:
        """
        Starts the browser session.

        Returns:
            Browser: The browser session.

        Raises:
            Exception: If there is an issue starting the browser session.
        """

    @abstractmethod
    def configure_context(self, browser: "Dendrite") -> None:
        """
        Configures the browser context.

        Args:
            browser (Dendrite): The browser to configure.

        Raises:
            Exception: If there is an issue configuring the browser context.
        """

    @abstractmethod
    def stop_session(self) -> None:
        """
        Stops the browser session.

        Raises:
            Exception: If there is an issue stopping the browser session.
        """
