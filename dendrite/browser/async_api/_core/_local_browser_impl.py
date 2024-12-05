from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union, overload
from loguru import logger
from typing_extensions import Literal

from dendrite.browser._common.constants import STEALTH_ARGS

if TYPE_CHECKING:
    from dendrite.browser.async_api._core.dendrite_browser import AsyncDendrite

from playwright.async_api import (
    Browser,
    Download,
    Playwright,
    BrowserContext,
    StorageState,
)

from dendrite.browser.async_api._core._impl_browser import ImplBrowser
from dendrite.browser.async_api._core._type_spec import PlaywrightPage

import tempfile
import shutil
import os


class LocalImpl(ImplBrowser):
    def __init__(self) -> None:
        pass

    async def start_browser(
        self,
        playwright: Playwright,
        pw_options: dict,
        storage_state: Optional[StorageState] = None,
    ) -> Browser:
        return await playwright.chromium.launch(**pw_options)

    async def get_download(
        self,
        dendrite_browser: "AsyncDendrite",
        pw_page: PlaywrightPage,
        timeout: float,
    ) -> Download:
        return await dendrite_browser._download_handler.get_data(pw_page, timeout)

    async def configure_context(self, browser: "AsyncDendrite"):
        pass

    async def stop_session(self):
        pass
