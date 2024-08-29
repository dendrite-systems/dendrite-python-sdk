import os
from typing import Any, Optional

from playwright.async_api import async_playwright

from dendrite_python_sdk._common.constants import STEALTH_ARGS
from dendrite_python_sdk._core._managers.active_page_manager import PageManager
from dendrite_python_sdk._core.dendrite_browser import DendriteBrowser


class DendriteRemoteBrowser(DendriteBrowser):
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        dendrite_api_key: Optional[str] = None,
        browserbase_api_key: Optional[str] = None,
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
        self.browserbase_api_key = browserbase_api_key
        if browserbase_api_key is None:
            self.browserbase_api_key = os.environ.get("BROWSERBASE_API_KEY")

        if self.browserbase_api_key is None:
            raise Exception("Please enter a Browserbase API key")

        self.session_id = None

    async def launch(self):
        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"
        self._playwright = await async_playwright().start()

        browser = await self._playwright.chromium.connect_over_cdp(
            self.get_browserbase_url(enable_proxy=True)
        )

        if self._auth_data:
            self._browser_context = await browser.new_context(
                storage_state=self._auth_data.to_storage_state(),
                user_agent=self._auth_data.user_agent,
            )
        else:
            self._browser_context = await browser.new_context()

        self._active_page_manager = PageManager(self, self._browser_context)
        return browser, self._browser_context, self._active_page_manager

    async def create_session(self) -> str:
        return await self._browser_api_client.send_request(
            "browser/sessions", method="POST"
        )

    async def get_download_session(self, session_id: str):
        return await self._browser_api_client.send_request(
            f"browser/sessions/{session_id}/download", method="GET"
        )

    def get_browserbase_url(self, enable_proxy: bool = False):
        base_url = f"wss://connect.browserbase.com?apiKey={self.browserbase_api_key}"

        if enable_proxy:
            base_url = base_url + "&enableProxy=true"

        return base_url

    async def start_remote_session(self, generate_session: bool = False) -> str:
        if generate_session:
            self.session_id = await self.create_session()
        base_url = self._browser_api_client.base_url.split("://", maxsplit=1)[1]
        url = f"ws://{base_url}/browser/ws"
        if self.session_id:
            url += f"?session_id={self.session_id}"
        print(f"Connecting to remote browser session at {url}")
        return url

    async def get_download(self):
        if self.session_id is None:
            raise Exception(
                "Session ID is not set. To download a session has to be started"
            )
        return await self.get_download_session(self.session_id)
