from typing import TYPE_CHECKING
from playwright.async_api import Browser, Playwright, Download

from abc import ABC, abstractmethod

from dendrite_sdk.async_api._core._type_spec import PlaywrightPage

if TYPE_CHECKING:
    from dendrite_sdk.async_api._core.dendrite_remote_browser import (
        AsyncDendriteRemoteBrowser,
    )


class RemoteProvider(ABC):
    @abstractmethod
    async def _close(self, AsyncDendriteRemoteBrowser):
        pass

    @abstractmethod
    async def _start_browser(self, playwright: Playwright) -> Browser:
        pass

    @abstractmethod
    async def configure_context(self, browser: "AsyncDendriteRemoteBrowser"):
        pass

    @abstractmethod
    async def get_download(
        self,
        AsyncDendriteRemoteBrowser,
        pw_page: PlaywrightPage,
        timeout: float = 30000,
    ) -> Download:
        pass
