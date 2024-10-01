from typing import TYPE_CHECKING
from playwright.sync_api import Browser, Playwright, Download
from abc import ABC, abstractmethod
from dendrite_sdk.sync_api._core._type_spec import PlaywrightPage

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
        self,
        dendrite_browser: DendriteRemoteBrowser,
        pw_page: PlaywrightPage,
        timeout: float = 30000,
    ) -> Download:
        pass
