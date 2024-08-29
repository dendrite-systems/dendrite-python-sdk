from typing import Generic, TypeVar, TYPE_CHECKING
from playwright.async_api import Browser, Playwright, BrowserContext

from abc import ABC, abstractmethod

from dendrite_python_sdk._core._type_spec import DownloadType

if TYPE_CHECKING:
    from dendrite_python_sdk._core.dendrite_remote_browser import DendriteRemoteBrowser


class RemoteProvider(ABC, Generic[DownloadType]):
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
    async def get_download(self, DendriteRemoteBrowser) -> DownloadType:
        pass
