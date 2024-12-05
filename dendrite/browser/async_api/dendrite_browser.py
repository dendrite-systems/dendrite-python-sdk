import os
import pathlib
import re
from abc import ABC
from typing import Any, List, Optional, Sequence, Union
from uuid import uuid4

from loguru import logger
from playwright.async_api import (
    Download,
    Error,
    FileChooser,
    FilePayload,
    StorageState,
    async_playwright,
)

from dendrite.browser._common._exceptions.dendrite_exception import (
    BrowserNotLaunchedError,
    DendriteException,
    IncorrectOutcomeError,
)
from dendrite.browser._common.constants import STEALTH_ARGS
from dendrite.browser.async_api._utils import get_domain_w_suffix
from dendrite.browser.remote import Providers
from dendrite.logic.config import Config
from dendrite.logic import AsyncLogicEngine

from ._event_sync import EventSync
from .browser_impl.impl_mapping import get_impl
from .dendrite_page import AsyncPage
from .manager.page_manager import PageManager
from .mixin import (
    AskMixin,
    ClickMixin,
    ExtractionMixin,
    FillFieldsMixin,
    GetElementMixin,
    KeyboardMixin,
    MarkdownMixin,
    ScreenshotMixin,
    WaitForMixin,
)
from .protocol.browser_protocol import BrowserProtocol
from .types import PlaywrightPage


class AsyncDendrite(
    ScreenshotMixin,
    WaitForMixin,
    MarkdownMixin,
    ExtractionMixin,
    AskMixin,
    FillFieldsMixin,
    ClickMixin,
    KeyboardMixin,
    GetElementMixin,
    ABC,
):
    """
    AsyncDendrite is a class that manages a browser instance using Playwright, allowing
    interactions with web pages using natural language.

    This class handles initialization with API keys for Dendrite, OpenAI, and Anthropic, manages browser
    contexts, and provides methods for navigation, authentication, and other browser-related tasks.

    Attributes:
        id (UUID): The unique identifier for the AsyncDendrite instance.
        auth_data (Optional[AuthSession]): The authentication session data for the browser.
        dendrite_api_key (str): The API key for Dendrite, used for interactions with the Dendrite API.
        playwright_options (dict): Options for configuring the Playwright browser instance.
        playwright (Optional[Playwright]): The Playwright instance managing the browser.
        browser_context (Optional[BrowserContext]): The current browser context, which may include cookies and other session data.
        active_page_manager (Optional[PageManager]): The manager responsible for handling active pages within the browser context.
        user_id (Optional[str]): The user ID associated with the browser session.
        browser_api_client (BrowserAPIClient): The API client used for communicating with the Dendrite API.
        api_config (APIConfig): The configuration for the language models, including API keys for OpenAI and Anthropic.

    Raises:
        Exception: If any of the required API keys (Dendrite, OpenAI, Anthropic) are not provided or found in the environment variables.
    """

    def __init__(
        self,
        playwright_options: Any = {
            "headless": False,
            "args": STEALTH_ARGS,
        },
        remote_config: Optional[Providers] = None,
        config: Optional[Config] = None,
        auth: Optional[Union[List[str], str]] = None,
    ):
        """
        Initialize AsyncDendrite with optional domain authentication.

        Args:
            playwright_options: Options for configuring Playwright
            remote_config: Remote browser provider configuration
            config: Configuration object
            auth: List of domains or single domain to load authentication state for
        """
        self._impl = self._get_impl(remote_config)
        self._playwright_options = playwright_options
        self._config = config or Config()
        auth_url = [auth] if isinstance(auth, str) else auth or []
        self._auth_domains = [get_domain_w_suffix(url) for url in auth_url]

        self._id = uuid4().hex
        self._active_page_manager: Optional[PageManager] = None
        self._user_id: Optional[str] = None
        self._upload_handler = EventSync(event_type=FileChooser)
        self._download_handler = EventSync(event_type=Download)
        self.closed = False
        self._browser_api_client: AsyncLogicEngine = AsyncLogicEngine(self._config)

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

    @property
    def logic_engine(self) -> AsyncLogicEngine:
        return self._browser_api_client

    @property
    def dendrite_browser(self) -> "AsyncDendrite":
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Ensure cleanup is handled
        await self.close()

    def _get_impl(self, remote_provider: Optional[Providers]) -> BrowserProtocol:
        # if remote_provider is None:)
        return get_impl(remote_provider)

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
            url, new_tab=True, timeout=timeout, expected_page=expected_page
        )

    async def goto(
        self,
        url: str,
        new_tab: bool = False,
        timeout: Optional[float] = 15000,
        expected_page: str = "",
    ) -> AsyncPage:
        """
        Navigates to the specified URL, optionally in a new tab

        Args:
            url (str): The URL to navigate to.
            new_tab (bool, optional): Whether to open the URL in a new tab. Defaults to False.
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

        if new_tab:
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

    async def scroll_to_bottom(
        self,
        timeout: float = 30000,
        scroll_increment: int = 1000,
        no_progress_limit: int = 3,
    ):
        """
        Scrolls to the bottom of the current page.

        Returns:
            None
        """
        active_page = await self.get_active_page()
        await active_page.scroll_to_bottom(
            timeout=timeout,
            scroll_increment=scroll_increment,
            no_progress_limit=no_progress_limit,
        )

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
        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"
        self._playwright = await async_playwright().start()

        # Get and merge storage states for authenticated domains
        storage_states = []
        for domain in self._auth_domains:
            state = await self._get_domain_storage_state(domain)

            if state:
                storage_states.append(state)

        # Launch browser
        browser = await self._impl.start_browser(
            self._playwright, self._playwright_options
        )

        # Create context with merged storage state if available
        if storage_states:
            merged_state = await self._merge_storage_states(storage_states)
            self.browser_context = await browser.new_context(storage_state=merged_state)
        else:
            self.browser_context = (
                browser.contexts[0]
                if len(browser.contexts) > 0
                else await browser.new_context()
            )

        self._active_page_manager = PageManager(self, self.browser_context)
        await self._impl.configure_context(self)

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
        Closes the browser and updates storage states for authenticated domains before cleanup.

        This method updates the storage states for authenticated domains, stops the Playwright
        instance, and closes the browser context.

        Returns:
            None

        Raises:
            Exception: If there is an issue closing the browser or updating session data.
        """
        self.closed = True

        try:
            if self.browser_context and self._auth_domains:
                # Update storage state for each authenticated domain
                for domain in self._auth_domains:
                    await self.save_auth(domain)

                await self._impl.stop_session()
                await self.browser_context.close()
        except Error:
            pass

        try:
            if self._playwright:
                await self._playwright.stop()
        except (AttributeError, Exception):
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

    async def get_download(self, timeout: float) -> Download:
        """
        Retrieves the download event from the browser.

        Returns:
            Download: The download event.

        Raises:
            Exception: If there is an issue retrieving the download event.
        """
        active_page = await self.get_active_page()
        pw_page = active_page.playwright_page
        return await self._get_download(pw_page, timeout)

    async def _get_download(self, pw_page: PlaywrightPage, timeout: float) -> Download:
        """
        Retrieves the download event from the browser.

        Returns:
            Download: The download event.

        Raises:
            Exception: If there is an issue retrieving the download event.
        """
        return await self._download_handler.get_data(pw_page, timeout=timeout)

    async def upload_files(
        self,
        files: Union[
            str,
            pathlib.Path,
            FilePayload,
            Sequence[Union[str, pathlib.Path]],
            Sequence[FilePayload],
        ],
        timeout: float = 30000,
    ) -> None:
        """
        Uploads files to the active page using a file chooser.

        Args:
            files (Union[str, pathlib.Path, FilePayload, Sequence[Union[str, pathlib.Path]], Sequence[FilePayload]]): The file(s) to be uploaded.
                This can be a file path, a `FilePayload` object, or a sequence of file paths or `FilePayload` objects.
            timeout (float, optional): The maximum amount of time (in milliseconds) to wait for the file chooser to be ready. Defaults to 30.

        Returns:
            None
        """
        page = await self.get_active_page()

        file_chooser = await self._get_filechooser(page.playwright_page, timeout)
        await file_chooser.set_files(files)

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

    async def save_auth(self, url: str) -> None:
        """
        Save authentication state for a specific domain.

        Args:
            domain (str): Domain to save authentication for (e.g., "github.com")
        """
        if not self.browser_context:
            raise DendriteException("Browser context not initialized")

        domain = get_domain_w_suffix(url)

        # Get current storage state
        storage_state = await self.browser_context.storage_state()

        # Filter storage state for specific domain
        filtered_state = {
            "origins": [
                origin
                for origin in storage_state.get("origins", [])
                if domain in origin.get("origin", "")
            ],
            "cookies": [
                cookie
                for cookie in storage_state.get("cookies", [])
                if domain in cookie.get("domain", "")
            ],
        }

        # Save to cache
        self._config.storage_cache.set(
            {"domain": domain}, StorageState(**filtered_state)
        )

    async def setup_auth(
        self,
        url: str,
        message: str = "Please log in to the website. Once done, press Enter to continue...",
    ) -> None:
        """
        Set up authentication for a specific URL.

        Args:
            url (str): URL to navigate to for login
            message (str): Message to show while waiting for user input
        """
        # Extract domain from URL
        # domain = urlparse(url).netloc
        # if not domain:
        #     domain = urlparse(f"https://{url}").netloc

        domain = get_domain_w_suffix(url)

        try:
            # Start Playwright
            self._playwright = await async_playwright().start()

            # Launch browser with normal context
            browser = await self._impl.start_browser(
                self._playwright, {**self._playwright_options, "headless": False}
            )

            self.browser_context = await browser.new_context()
            self._active_page_manager = PageManager(self, self.browser_context)

            # Navigate to login page
            await self.goto(url)

            # Wait for user to complete login
            print(message)
            input()

            # Save the storage state for this domain
            await self.save_auth(domain)

        finally:
            # Clean up
            await self.close()

    async def _get_domain_storage_state(self, domain: str) -> Optional[StorageState]:
        """Get storage state for a specific domain"""
        return self._config.storage_cache.get({"domain": domain}, index=0)

    async def _merge_storage_states(self, states: List[StorageState]) -> StorageState:
        """Merge multiple storage states into one"""
        merged = {"origins": [], "cookies": []}
        seen_origins = set()
        seen_cookies = set()

        for state in states:
            # Merge origins
            for origin in state.get("origins", []):
                origin_key = origin.get("origin", "")
                if origin_key not in seen_origins:
                    merged["origins"].append(origin)
                    seen_origins.add(origin_key)

            # Merge cookies
            for cookie in state.get("cookies", []):
                cookie_key = (
                    f"{cookie.get('name')}:{cookie.get('domain')}:{cookie.get('path')}"
                )
                if cookie_key not in seen_cookies:
                    merged["cookies"].append(cookie)
                    seen_cookies.add(cookie_key)

        return StorageState(**merged)
