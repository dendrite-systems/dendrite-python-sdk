from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dendrite_sdk.sync_api._core.dendrite_browser import Dendrite
from dendrite_sdk.sync_api._core._type_spec import PlaywrightPage
from playwright.sync_api import Download, Browser, Playwright


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
        pass

    @abstractmethod
    def start_browser(self, playwright: Playwright, pw_options: dict) -> Browser:
        """
        Starts the browser session.

        Returns:
            Browser: The browser session.

        Raises:
            Exception: If there is an issue starting the browser session.
        """
        pass

    @abstractmethod
    def configure_context(self, browser: "Dendrite") -> None:
        """
        Configures the browser context.

        Args:
            browser (Dendrite): The browser to configure.

        Raises:
            Exception: If there is an issue configuring the browser context.
        """
        pass

    @abstractmethod
    def stop_session(self) -> None:
        """
        Stops the browser session.

        Raises:
            Exception: If there is an issue stopping the browser session.
        """
        pass


class LocalImpl(ImplBrowser):

    def __init__(self) -> None:
        pass

    def start_browser(self, playwright: Playwright, pw_options) -> Browser:
        return playwright.chromium.launch(**pw_options)

    def get_download(
        self, dendrite_browser: "Dendrite", pw_page: PlaywrightPage, timeout: float
    ) -> Download:
        return dendrite_browser._download_handler.get_data(pw_page, timeout)

    def configure_context(self, browser: "Dendrite"):
        pass

    def stop_session(self):
        pass
