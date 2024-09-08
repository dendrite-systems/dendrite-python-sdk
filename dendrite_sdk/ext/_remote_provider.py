from typing import TYPE_CHECKING
from playwright.async_api import Browser, Playwright, Download

from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from dendrite_sdk._core.dendrite_remote_browser import DendriteRemoteBrowser


class RemoteProvider(ABC):
    @abstractmethod
    async def _close(self, DendriteRemoteBrowser):
        pass

    @abstractmethod
    async def _start_browser(self, playwright: Playwright) -> Browser:
        pass

    @abstractmethod
    async def configure_context(self, browser: "DendriteRemoteBrowser"):
        pass

    @abstractmethod
    async def get_download(
        self, DendriteRemoteBrowser, timeout: float = 30000
    ) -> Download:
        pass
