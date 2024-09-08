from typing import Any, Optional

from dendrite_sdk._core.dendrite_remote_browser import DendriteRemoteBrowser
from dendrite_sdk.ext.browserbase._provider import BrowserbaseProvider
from dendrite_sdk.ext.browserbase._download import BrowserbaseDownload


class BrowserbaseBrowser(DendriteRemoteBrowser[BrowserbaseProvider]):
    def __init__(
        self,
        enable_proxy: bool = False,
        enable_downloads: bool = False,
        browserbase_api_key: Optional[str] = None,
        browserbase_project_id: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        dendrite_api_key: Optional[str] = None,
        playwright_options: Any = ...,
    ):
        provider = BrowserbaseProvider(
            enable_downloads=enable_downloads,
            enable_proxy=enable_proxy,
            api_key=browserbase_api_key,
            project_id=browserbase_project_id,
        )
        super().__init__(
            provider,
            openai_api_key,
            anthropic_api_key,
            dendrite_api_key,
            playwright_options,
        )
