from typing import TYPE_CHECKING
from playwright.sync_api import Browser, Playwright, Download, Page
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from dendrite_sdk.sync_api._core.dendrite_remote_browser import (
        DendriteRemoteBrowser,
    )


class RemoteProvider(ABC):

    @abstractmethod
    def _close(self, AsyncDendriteRemoteBrowser):
        pass

    @abstractmethod
    def _start_browser(self, playwright: Playwright) -> Browser:
        pass

    @abstractmethod
    def configure_context(self, browser: "DendriteRemoteBrowser"):
        pass

    @abstractmethod
    def get_download(
        self, AsyncDendriteRemoteBrowser, pw_page: Page, timeout: float = 30000
    ) -> Download:
        pass
