from typing import Any, Type

from dendrite_python_sdk._common.constants import STEALTH_ARGS
from dendrite_python_sdk._core.dendrite_remote_browser import DendriteRemoteBrowser
from dendrite_python_sdk.ext.browser_base.provider import BrowserBaseProvider
from dendrite_python_sdk.ext.browser_base.download import BrowserBaseDownload


class BrowserBaseBrowser(
    DendriteRemoteBrowser[BrowserBaseProvider, BrowserBaseDownload]
):
    def __init__(
        self,
        enable_proxy: bool = False,
        enable_downloads: bool = False,
        browserbase_api_key: str | None = None,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
        dendrite_api_key: str | None = None,
        playwright_options: Any = ...,
    ):
        provider = BrowserBaseProvider(
            enable_downloads=enable_downloads,
            enable_proxy=enable_proxy,
            api_key=browserbase_api_key,
        )
        super().__init__(
            provider,
            openai_api_key,
            anthropic_api_key,
            dendrite_api_key,
            playwright_options,
        )
