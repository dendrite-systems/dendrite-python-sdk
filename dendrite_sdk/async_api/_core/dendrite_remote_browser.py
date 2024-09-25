import os
from typing import Any, Generic, Optional, TypeVar

from playwright.async_api import async_playwright, Download, Page

from dendrite_sdk.async_api._common.constants import STEALTH_ARGS
from dendrite_sdk.async_api._core._managers.page_manager import PageManager
from dendrite_sdk.async_api._core._base_browser import BaseAsyncDendriteBrowser
from dendrite_sdk.async_api.ext._remote_provider import RemoteProvider

T = TypeVar("T", bound=RemoteProvider)


class AsyncDendriteRemoteBrowser(BaseAsyncDendriteBrowser, Generic[T]):
    def __init__(
        self,
        provider: T,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        dendrite_api_key: Optional[str] = None,
        playwright_options: Any = {
            "headless": False,
            "args": STEALTH_ARGS,
        },
    ):
        super().__init__(
            openai_api_key=openai_api_key,
            dendrite_api_key=dendrite_api_key,
            anthropic_api_key=anthropic_api_key,
            playwright_options=playwright_options,
        )

        self._provider: T = provider

    async def _launch(self):
        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"
        self._playwright = await async_playwright().start()
        browser = await self._provider._start_browser(self._playwright)

        if self._auth:
            auth_session = await self._get_auth_session(self._auth)
            self.browser_context = await browser.new_context(
                storage_state=auth_session.to_storage_state(),
                user_agent=auth_session.user_agent,
            )
        else:
            self.browser_context = browser.contexts[0]

        self._active_page_manager = PageManager(self, self.browser_context)

        await self._provider.configure_context(self)

        return browser, self.browser_context, self._active_page_manager

    async def _close(self):
        await self._provider._close(self)
        await super().close()

    async def _get_download(self, pw_page: Page, timeout: float) -> Download:
        return await self._provider.get_download(self, pw_page, timeout)
