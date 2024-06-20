

import os
from typing import Any, Optional
from dendrite_python_sdk.dendrite_browser.ActivePageManager import ActivePageManager
from dendrite_python_sdk.dendrite_browser.DendriteBrowser import DendriteBrowser
from playwright.async_api import async_playwright, Playwright, BrowserContext

from dendrite_python_sdk.request_handler import browser_ws_uri, create_session

from ..browserbase import session


class DendriteRemoteBrowser(DendriteBrowser):
    def __init__(
        self,
        openai_api_key: str,
        id=None,
        dendrite_api_key: Optional[str] = None,
        playwright_options: Any = {
            "headless": False,
        },
    ):
        super().__init__(
            openai_api_key=openai_api_key,
            dendrite_api_key=dendrite_api_key,
            playwright_options=playwright_options,
        )

    async def launch(self):
        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"
        self.playwright = await async_playwright().start()
        browser = await self.playwright.chromium.connect_over_cdp(await self.start_remote_session(generate_session=True))
        self.browser_context = await browser.new_context()
        await self.browser_context.add_init_script(path="dendrite_python_sdk/dendrite_browser/scripts/eventListenerPatch.js")
        self.active_page_manager = ActivePageManager(self, self.browser_context)
        return browser, self.browser_context, self.active_page_manager 
    
    async def start_remote_session(self, generate_session: bool = False) -> str:
        session_id = None
        if generate_session:
            session_id = await create_session()
        self.session_id = session_id
        uri = await browser_ws_uri(session_id)
        print(f"Connecting to remote browser session at {uri}")
        return uri
    
    async def get_download(self):
       if self.session_id is None:
           raise Exception("Session ID is not set. To download a session has to be started")
       await session.get_download(self.session_id)
