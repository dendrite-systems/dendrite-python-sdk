import logging
from typing import Any, Optional, Union
from uuid import uuid4
import os
from playwright.async_api import async_playwright, Playwright, BrowserContext

from dendrite_python_sdk.dto.AuthenticateDTO import AuthenticateDTO
from dendrite_python_sdk.dto.UploadAuthSessionDTO import UploadAuthSessionDTO
from dendrite_python_sdk.dendrite_browser.ActivePageManager import (
    ActivePageManager,
)
from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage
from dendrite_python_sdk.dendrite_browser.constants import STEALTH_ARGS
from dendrite_python_sdk.dendrite_browser.authentication.auth_session import (
    AuthSession,
)
from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.dendrite_browser.browser_api_client import BrowserAPIClient


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DendriteBrowser:
    def __init__(
        self,
        id=None,
        openai_api_key: Optional[str] = None,
        dendrite_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        playwright_options: Any = {
            "headless": False,
            "args": STEALTH_ARGS,
        },
    ):

        if not dendrite_api_key or dendrite_api_key == "":
            dendrite_api_key = os.environ.get("DENDRITE_API_KEY", "")
            if not dendrite_api_key or dendrite_api_key == "":
                raise Exception("Dendrite API key is required to use DendriteBrowser")

        if not anthropic_api_key or anthropic_api_key == "":
            anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if anthropic_api_key == "":
                raise Exception("Anthropic API key is required to use DendriteBrowser")

        if not openai_api_key or openai_api_key == "":
            openai_api_key = os.environ.get("OPENAI_API_KEY", "")
            if not openai_api_key or openai_api_key == "":
                raise Exception("OpenAI API key is required to use DendriteBrowser")

        self.id = uuid4() if id == None else id
        self.auth_data: Optional[AuthSession] = None
        self.dendrite_api_key = dendrite_api_key
        self.playwright_options = playwright_options
        self.playwright: Optional[Playwright] = None
        self.browser_context: Optional[BrowserContext] = None
        self.active_page_manager: Optional[ActivePageManager] = None
        self.user_id: Optional[str] = None
        self.browser_api_client = BrowserAPIClient(dendrite_api_key)

        llm_config = LLMConfig(
            openai_api_key=openai_api_key, anthropic_api_key=anthropic_api_key
        )
        self.llm_config = llm_config

    async def get_active_page(self) -> DendritePage:
        active_page_manager = await self._get_active_page_manager()
        return await active_page_manager.get_active_page()

    def get_llm_config(self):
        return self.llm_config

    async def goto(
        self,
        url: str,
        new_page: bool = False,
        scroll_through_entire_page: Optional[bool] = False,
        timeout: Optional[float] = 15000,
        expected_page: str = "",
    ) -> DendritePage:
        active_page_manager = await self._get_active_page_manager()

        if new_page:
            active_page = await active_page_manager.open_new_page()
        else:
            active_page = await active_page_manager.get_active_page()
        try:
            await active_page.page.goto(url, timeout=timeout)
        except TimeoutError:
            print("Timeout when loading page but continuing anyways.")
        except Exception as e:
            print(f"Timeout when loading page but continuing anyways. {e}")

        if scroll_through_entire_page:
            await active_page.scroll_through_entire_page()

        page = await active_page_manager.get_active_page()
        if expected_page != "":
            try:
                prompt = f"We are checking if we have arrived on the expected type of page. If it is apparent that we have arrived on the wrong page, output an error. Here is the description: '{expected_page}'"
                await page.ask(prompt, bool)
            except Exception as e:
                raise Exception(f"Incorrect navigation, reason: {e}")

        return page

    def _is_launched(self):
        return self.browser_context != None

    async def _get_active_page_manager(self) -> ActivePageManager:
        if not self.active_page_manager:
            _, _, active_page_manager = await self.launch()
            return active_page_manager
        else:
            return self.active_page_manager

    async def launch(self):
        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"
        self.playwright = await async_playwright().start()
        browser = await self.playwright.chromium.launch(**self.playwright_options)

        if self.auth_data:
            self.browser_context = await browser.new_context(
                storage_state=self.auth_data.to_storage_state(),
                user_agent=self.auth_data.user_agent,
            )
        else:
            self.browser_context = await browser.new_context()

        self.active_page_manager = ActivePageManager(self, self.browser_context)
        return browser, self.browser_context, self.active_page_manager

    async def authenticate(self, domains: Union[str, list[str]]):
        dto = AuthenticateDTO(domains=domains)
        auth_session: AuthSession = await self.browser_api_client.authenticate(dto)
        self.auth_data = auth_session

    async def new_page(self) -> DendritePage:
        active_page_manager = await self._get_active_page_manager()
        return await active_page_manager.open_new_page()

    async def add_cookies(self, cookies):
        if not self.browser_context:
            raise Exception("Browser context not initialized")

        await self.browser_context.add_cookies(cookies)

    async def close(self):
        if self.browser_context:
            if self.auth_data:
                storage_state = await self.browser_context.storage_state()
                dto = UploadAuthSessionDTO(
                    auth_data=self.auth_data, storage_state=storage_state
                )
                await self.browser_api_client.upload_auth_session(dto)
            await self.browser_context.close()

        if self.playwright:
            await self.playwright.stop()

    async def get_download(self):
        pass
