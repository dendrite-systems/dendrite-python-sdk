from typing import TYPE_CHECKING, Optional, Protocol, Union
from typing_extensions import Literal
from dendrite.browser.remote import Providers

if TYPE_CHECKING:
    from ..dendrite_browser import Dendrite
from playwright.sync_api import Browser, Download, Playwright
from ..types import PlaywrightPage


class BrowserProtocol(Protocol):

    def __init__(self, settings: Providers) -> None: ...

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
        ...

    def start_browser(self, playwright: Playwright, pw_options: dict) -> Browser:
        """
        Starts the browser session.

        Args:
            playwright: The playwright instance
            pw_options: Playwright launch options

        Returns:
            Browser: A Browser instance
        """
        ...

    def configure_context(self, browser: "Dendrite") -> None:
        """
        Configures the browser context.

        Args:
            browser (Dendrite): The browser to configure.

        Raises:
            Exception: If there is an issue configuring the browser context.
        """
        ...

    def stop_session(self) -> None:
        """
        Stops the browser session.

        Raises:
            Exception: If there is an issue stopping the browser session.
        """
        ...
