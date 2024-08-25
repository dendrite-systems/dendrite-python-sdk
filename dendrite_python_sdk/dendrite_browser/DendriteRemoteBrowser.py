import os
from playwright.async_api import async_playwright
from typing import Any, Optional

from dendrite_python_sdk.dendrite_browser.ActivePageManager import ActivePageManager
from dendrite_python_sdk.dendrite_browser.DendriteBrowser import DendriteBrowser


class DendriteRemoteBrowser(DendriteBrowser):
    def __init__(
        self,
        openai_api_key: str,
        anthropic_api_key: Optional[str] = None,
        dendrite_api_key: Optional[str] = None,
        playwright_options: Any = {
            "headless": False,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--no-first-run",
                "--no-service-autorun",
                "--no-default-browser-check",
                "--homepage=about:blank",
                "--no-pings",
                "--password-store=basic",
                "--disable-infobars",
                "--disable-breakpad",
                "--disable-component-update",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-background-networking",
                "--disable-dev-shm-usage",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-session-crashed-bubble",
            ],
        },
    ):
        super().__init__(
            openai_api_key=openai_api_key,
            dendrite_api_key=dendrite_api_key,
            anthropic_api_key=anthropic_api_key,
            playwright_options=playwright_options,
        )
        self.session_id = None

    async def launch(self):
        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"
        self.playwright = await async_playwright().start()

        browser = await self.playwright.chromium.connect_over_cdp(
            self.get_browserbase_url(enable_proxy=True)
        )

        if self.auth_data:
            self.browser_context = await browser.new_context(
                storage_state=self.auth_data.to_storage_state(),
                user_agent=self.auth_data.user_agent,
            )
        else:
            self.browser_context = await browser.new_context()

        await self.browser_context.add_init_script(
            path="dendrite_server/core/browser/scripts/eventListenerPatch.js"
        )

        self.active_page_manager = ActivePageManager(self, self.browser_context)
        return browser, self.browser_context, self.active_page_manager

    async def create_session(self) -> str:
        return await self.browser_api_client.send_request(
            "browser/sessions", method="POST"
        )

    async def get_download_session(self, session_id: str):
        return await self.browser_api_client.send_request(
            f"browser/sessions/{session_id}/download", method="GET"
        )

    def get_browserbase_url(self, enable_proxy: bool = False):
        base_url = os.environ.get("BROWSERBASE_CONNECTION_URI")
        if base_url is None:
            raise Exception("BROWSERBASE_CONNECTION_URI not set")

        if enable_proxy:
            base_url = base_url + "&enableProxy=true"

        return base_url

    async def start_remote_session(self, generate_session: bool = False) -> str:
        if generate_session:
            self.session_id = await self.create_session()
        base_url = self.browser_api_client.base_url.split("://", maxsplit=1)[1]
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
