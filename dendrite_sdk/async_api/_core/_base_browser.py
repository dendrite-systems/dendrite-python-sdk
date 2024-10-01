from abc import ABC, abstractmethod
import re
from typing import Any, List, Literal, Optional, Union
from uuid import uuid4
import os
from loguru import logger
from playwright.async_api import (
    async_playwright,
    Playwright,
    BrowserContext,
    FileChooser,
    Download,
)

from dendrite_sdk.async_api._api.dto.authenticate_dto import AuthenticateDTO
from dendrite_sdk.async_api._api.dto.upload_auth_session_dto import UploadAuthSessionDTO
from dendrite_sdk.async_api._common.event_sync import EventSync
from dendrite_sdk.async_api._core._managers.page_manager import (
    PageManager,
)

from dendrite_sdk.async_api._core._type_spec import PlaywrightPage
from dendrite_sdk.async_api._core.dendrite_page import AsyncPage
from dendrite_sdk.async_api._common.constants import STEALTH_ARGS
from dendrite_sdk.async_api._core.mixin.ask import AskMixin
from dendrite_sdk.async_api._core.mixin.click import ClickMixin
from dendrite_sdk.async_api._core.mixin.extract import ExtractionMixin
from dendrite_sdk.async_api._core.mixin.fill_fields import FillFieldsMixin
from dendrite_sdk.async_api._core.mixin.get_element import GetElementMixin
from dendrite_sdk.async_api._core.mixin.keyboard import KeyboardMixin
from dendrite_sdk.async_api._core.mixin.wait_for import WaitForMixin
from dendrite_sdk.async_api._core.models.authentication import (
    AuthSession,
)

from dendrite_sdk.async_api._core.models.api_config import APIConfig
from dendrite_sdk.async_api._api.browser_api_client import BrowserAPIClient
from dendrite_sdk._common._exceptions.dendrite_exception import (
    BrowserNotLaunchedError,
    DendriteException,
    IncorrectOutcomeError,
)


class BaseAsyncDendrite(
    ExtractionMixin,
    WaitForMixin,
    AskMixin,
    FillFieldsMixin,
    ClickMixin,
    KeyboardMixin,
    GetElementMixin,
    ABC,
):
    """
    BaseAsyncDendrite is an abstract base class that manages a browser instance using Playwright, allowing
    interactions with web pages using natural language.

    This class handles initialization with API keys for Dendrite, OpenAI, and Anthropic, manages browser
    contexts, and provides methods for navigation, authentication, and other browser-related tasks.

    Attributes:
        playwright (Optional[Playwright]): The Playwright instance managing the browser.
        browser_context (Optional[BrowserContext]): The current browser context, which may include cookies and other session data.
        closed (bool): Indicates whether the browser instance is closed.
        active_page_manager (Optional[PageManager]): The manager responsible for handling active pages within the browser context.
        user_id (Optional[str]): The user ID associated with the browser session.
        browser_api_client (BrowserAPIClient): The API client used for communicating with the Dendrite API.
        api_config (APIConfig): The configuration for the language models, including API keys for OpenAI and Anthropic.

    Raises:
        MissingApiKeyError: If any of the required API keys (Dendrite, OpenAI, Anthropic) are not provided or found in the environment variables.
    """

    def __init__(
        self,
        auth: Optional[Union[str, List[str]]] = None,
        dendrite_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        playwright_options: Any = {
            "headless": False,
            "args": STEALTH_ARGS,
        },
    ):
        """
        Initializes the BaseAsyncDendrite with API keys and Playwright options.

        Args:
            auth (Optional[Union[str, List[str]]]): The domains on which the browser should try and authenticate on.
            openai_api_key (Optional[str], optional): The OpenAI API key. If not provided, it's fetched from the environment variables.
            dendrite_api_key (Optional[str], optional): The Dendrite API key. If not provided, it's fetched from the environment variables.
            anthropic_api_key (Optional[str], optional): The Anthropic API key. If not provided, it's fetched from the environment variables.
            playwright_options (Any, optional): Options for configuring Playwright. Defaults to running in non-headless mode with stealth arguments.

        Raises:
            MissingApiKeyError: If any of the required API keys (Dendrite, OpenAI, Anthropic) are not provided or found in the environment variables.
        """

        api_config = APIConfig(
            dendrite_api_key=dendrite_api_key or os.environ.get("DENDRITE_API_KEY"),
            openai_api_key=openai_api_key or os.environ.get("OPENAI_API_KEY"),
            anthropic_api_key=anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY"),
        )

        self.api_config = api_config
        self.playwright: Optional[Playwright] = None
        self.browser_context: Optional[BrowserContext] = None

        self._id = uuid4().hex
        self._playwright_options = playwright_options
        self._active_page_manager: Optional[PageManager] = None
        self._user_id: Optional[str] = None
        self._upload_handler = EventSync(event_type=FileChooser)
        self._download_handler = EventSync(event_type=Download)
        self.closed = False
        self._auth = auth
        self._browser_api_client = BrowserAPIClient(api_config, self._id)

    @property
    def pages(self) -> List[AsyncPage]:
        """
        Retrieves the list of active pages managed by the PageManager.

        Returns:
            List[AsyncPage]: The list of active pages.
        """
        if self._active_page_manager:
            return self._active_page_manager.pages
        else:
            raise BrowserNotLaunchedError()

    async def _get_page(self) -> AsyncPage:
        active_page = await self.get_active_page()
        return active_page

    def _get_browser_api_client(self) -> BrowserAPIClient:
        return self._browser_api_client

    def _get_dendrite_browser(self) -> "BaseAsyncDendrite":
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Ensure cleanup is handled
        await self.close()

    async def _get_auth_session(self, domains: Union[str, list[str]]):
        dto = AuthenticateDTO(domains=domains)
        auth_session: AuthSession = await self._browser_api_client.authenticate(dto)
        return auth_session

    async def get_active_page(self) -> AsyncPage:
        """
        Retrieves the currently active page managed by the PageManager.

        Returns:
            AsyncPage: The active page object.

        Raises:
            Exception: If there is an issue retrieving the active page.
        """

        active_page_manager = await self._get_active_page_manager()
        return await active_page_manager.get_active_page()

    async def new_page(self) -> AsyncPage:
        """
        Opens a new page in the browser.

        Returns:
            AsyncPage: The newly opened page.

        Raises:
            Exception: If there is an issue opening a new page.
        """
        active_page_manager = await self._get_active_page_manager()
        return await active_page_manager.new_page()

    async def new_tab(
        self,
        url: str,
        timeout: Optional[float] = 15000,
        expected_page: str = "",
    ) -> AsyncPage:
        """
        Opens a new tab and navigates to the specified URL.

        Args:
            url (str): The URL to navigate to.
            timeout (Optional[float], optional): The maximum time (in milliseconds) to wait for the page to load. Defaults to 15000.
            expected_page (str, optional): A description of the expected page type for verification. Defaults to an empty string.

        Returns:
            AsyncPage: The page object after navigation.

        Raises:
            Exception: If there is an error during navigation or if the expected page type is not found.
        """
        return await self.goto(
            url, new_page=True, timeout=timeout, expected_page=expected_page
        )

    async def goto(
        self,
        url: str,
        new_page: bool = False,
        timeout: Optional[float] = 15000,
        expected_page: str = "",
    ) -> AsyncPage:
        """
        Navigates to the specified URL, optionally in a new tab

        Args:
            url (str): The URL to navigate to.
            new_page (bool, optional): Whether to open the URL in a new page. Defaults to False.
            timeout (Optional[float], optional): The maximum time (in milliseconds) to wait for the page to load. Defaults to 15000.
            expected_page (str, optional): A description of the expected page type for verification. Defaults to an empty string.

        Returns:
            AsyncPage: The page object after navigation.

        Raises:
            Exception: If there is an error during navigation or if the expected page type is not found.
        """
        # Check if the URL has a protocol
        if not re.match(r"^\w+://", url):
            url = f"https://{url}"

        active_page_manager = await self._get_active_page_manager()

        if new_page:
            active_page = await active_page_manager.new_page()
        else:
            active_page = await active_page_manager.get_active_page()
        try:
            logger.info(f"Going to {url}")
            await active_page.playwright_page.goto(url, timeout=timeout)
        except TimeoutError:
            logger.debug("Timeout when loading page but continuing anyways.")
        except Exception as e:
            logger.debug(f"Exception when loading page but continuing anyways. {e}")

        if expected_page != "":
            try:
                prompt = f"We are checking if we have arrived on the expected type of page. If it is apparent that we have arrived on the wrong page, output an error. Here is the description: '{expected_page}'"
                await active_page.ask(prompt, bool)
            except DendriteException as e:
                raise IncorrectOutcomeError(f"Incorrect navigation, reason: {e}")

        return active_page

    async def _launch(self):
        """
        Launches the Playwright instance and sets up the browser context and page manager.

        This method initializes the Playwright instance, creates a browser context, and sets up the PageManager.
        It also applies any authentication data if available.

        Returns:
            Tuple[Browser, BrowserContext, PageManager]: The launched browser, context, and page manager.

        Raises:
            Exception: If there is an issue launching the browser or setting up the context.
        """
        user_dir = "tmp/playwright"
        user_dir = os.path.join(os.getcwd(), user_dir)

        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"
        self._playwright = await async_playwright().start()
        # self.browser_context = (
        #     await self._playwright.chromium.launch_persistent_context(
        #         headless=False,
        #         user_data_dir=user_dir,
        #     )
        # )

        browser = await self._playwright.chromium.launch(**self._playwright_options)

        if self._auth:
            auth_session = await self._get_auth_session(self._auth)
            self.browser_context = await browser.new_context(
                storage_state=auth_session.to_storage_state(),
                user_agent=auth_session.user_agent,
            )
        else:
            self.browser_context = await browser.new_context()

        await self.browser_context.tracing.start(
            screenshots=True, snapshots=True, sources=True
        )
        self._active_page_manager = PageManager(self, self.browser_context)

        return browser, self.browser_context, self._active_page_manager

    async def add_cookies(self, cookies):
        """
        Adds cookies to the current browser context.

        Args:
            cookies (List[Dict[str, Any]]): A list of cookies to be added to the browser context.

        Raises:
            Exception: If the browser context is not initialized.
        """
        if not self.browser_context:
            raise DendriteException("Browser context not initialized")

        await self.browser_context.add_cookies(cookies)

    async def close(self):
        """
        Closes the browser and uploads authentication session data if available.

        This method stops the Playwright instance, closes the browser context, and uploads any
        stored authentication session data if applicable.

        Returns:
            None

        Raises:
            Exception: If there is an issue closing the browser or uploading session data.
        """

        self.closed = True
        if self.browser_context:
            if self._auth:
                auth_session = await self._get_auth_session(self._auth)
                storage_state = await self.browser_context.storage_state()
                dto = UploadAuthSessionDTO(
                    auth_data=auth_session, storage_state=storage_state
                )
                await self._browser_api_client.upload_auth_session(dto)
            await self.browser_context.close()
        try:
            if self._playwright:
                await self._playwright.stop()
        except AttributeError:
            pass

    def _is_launched(self):
        """
        Checks whether the browser context has been launched.

        Returns:
            bool: True if the browser context is launched, False otherwise.
        """
        return self.browser_context is not None

    async def _get_active_page_manager(self) -> PageManager:
        """
        Retrieves the active PageManager instance, launching the browser if necessary.

        Returns:
            PageManager: The active PageManager instance.

        Raises:
            Exception: If there is an issue launching the browser or retrieving the PageManager.
        """
        if not self._active_page_manager:
            _, _, active_page_manager = await self._launch()
            return active_page_manager

        return self._active_page_manager

    @abstractmethod
    async def _get_download(self, pw_page: PlaywrightPage, timeout: float) -> Download:
        """
        Retrieves the download event from the browser.

        Returns:
            Download: The download event.

        Raises:
            Exception: If there is an issue retrieving the download event.
        """
        pass

    async def _get_filechooser(
        self, pw_page: PlaywrightPage, timeout: float = 30000
    ) -> FileChooser:
        """
        Uploads files to the browser.

        Args:
            timeout (float): The maximum time to wait for the file chooser dialog. Defaults to 30000 milliseconds.

        Returns:
            FileChooser: The file chooser dialog.

        Raises:
            Exception: If there is an issue uploading files.
        """
        return await self._upload_handler.get_data(pw_page, timeout=timeout)
