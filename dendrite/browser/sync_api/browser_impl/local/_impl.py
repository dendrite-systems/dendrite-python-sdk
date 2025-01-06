from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union, overload
from loguru import logger
from typing_extensions import Literal
from dendrite.browser._common.constants import STEALTH_ARGS

if TYPE_CHECKING:
    from dendrite.browser.sync_api.dendrite_browser import Dendrite
import os
import shutil
import tempfile
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Download,
    Playwright,
    StorageState,
)
from dendrite.browser.sync_api.protocol.browser_protocol import BrowserProtocol
from dendrite.browser.sync_api.types import PlaywrightPage


class LocalImpl(BrowserProtocol):

    def __init__(self) -> None:
        pass

    def start_browser(
        self,
        playwright: Playwright,
        pw_options: dict,
        storage_state: Optional[StorageState] = None,
    ) -> Browser:
        return playwright.chromium.launch(**pw_options)

    def get_download(
        self, dendrite_browser: "Dendrite", pw_page: PlaywrightPage, timeout: float
    ) -> Download:
        return dendrite_browser._download_handler.get_data(pw_page, timeout)

    def configure_context(self, browser: "Dendrite"):
        pass

    def stop_session(self):
        pass
