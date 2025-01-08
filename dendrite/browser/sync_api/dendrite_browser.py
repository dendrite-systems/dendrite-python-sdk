import os
import pathlib
import re
from abc import ABC
from typing import Any, List, Optional, Sequence, Union
from uuid import uuid4
from loguru import logger
from playwright.sync_api import (
    Download,
    Error,
    FileChooser,
    FilePayload,
    StorageState,
    sync_playwright,
)
from dendrite.browser._common._exceptions.dendrite_exception import (
    BrowserNotLaunchedError,
    DendriteException,
    IncorrectOutcomeError,
)
from dendrite.browser._common.constants import STEALTH_ARGS
from dendrite.browser.sync_api._utils import get_domain_w_suffix
from dendrite.browser.remote import Providers
from dendrite.logic.config import Config
from dendrite.logic import LogicEngine
from ._event_sync import EventSync
from .browser_impl.impl_mapping import get_impl
from .dendrite_page import Page
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


class Dendrite(
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
    Dendrite is a class that manages a browser instance using Playwright, allowing
    interactions with web pages using natural language.

    This class handles initialization with configuration options, manages browser contexts,
    and provides methods for navigation, authentication, and other browser-related tasks.

    Attributes:
        id (str): The unique identifier for the Dendrite instance.
        browser_context (Optional[BrowserContext]): The current browser context, which may include cookies and other session data.
        active_page_manager (Optional[PageManager]): The manager responsible for handling active pages within the browser context.
        user_id (Optional[str]): The user ID associated with the browser session.
        logic_engine (LogicEngine): The engine used for processing natural language interactions.
        closed (bool): Whether the browser instance has been closed.
    """

    def __init__(
        self,
        playwright_options: Any = {"headless": False, "args": STEALTH_ARGS},
        remote_config: Optional[Providers] = None,
        config: Optional[Config] = None,
        auth: Optional[Union[List[str], str]] = None,
    ):
        """
        Initialize Dendrite with optional domain authentication.

        Args:
            playwright_options (dict): Options for configuring Playwright browser instance.
                Defaults to non-headless mode with stealth arguments.
            remote_config (Optional[Providers]): Remote browser provider configuration.
                Defaults to None for local browser.
            config (Optional[Config]): Configuration object for the instance.
                Defaults to a new Config instance.
            auth (Optional[Union[List[str], str]]): List of domains or single domain
                to load authentication state for. Defaults to None.
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
        self._browser_api_client: LogicEngine = LogicEngine(self._config)

    @property
    def pages(self) -> List[Page]:
        """
        Retrieves the list of active pages managed by the PageManager.

        Returns:
            List[Page]: The list of active pages.
        """
        if self._active_page_manager:
            return self._active_page_manager.pages
        else:
            raise BrowserNotLaunchedError()

    def _get_page(self) -> Page:
        active_page = self.get_active_page()
        return active_page

    @property
    def logic_engine(self) -> LogicEngine:
        return self._browser_api_client

    @property
    def dendrite_browser(self) -> "Dendrite":
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_impl(self, remote_provider: Optional[Providers]) -> BrowserProtocol:
        return get_impl(remote_provider)

    def get_active_page(self) -> Page:
        """
        Retrieves the currently active page managed by the PageManager.

        Returns:
            Page: The active page object.

        Raises:
            Exception: If there is an issue retrieving the active page.
        """
        active_page_manager = self._get_active_page_manager()
        return active_page_manager.get_active_page()

    def new_tab(
        self, url: str, timeout: Optional[float] = 15000, expected_page: str = ""
    ) -> Page:
        """
        Opens a new tab and navigates to the specified URL.

        Args:
            url (str): The URL to navigate to.
            timeout (Optional[float], optional): The maximum time (in milliseconds) to wait for the page to load. Defaults to 15000.
            expected_page (str, optional): A description of the expected page type for verification. Defaults to an empty string.

        Returns:
            Page: The page object after navigation.

        Raises:
            Exception: If there is an error during navigation or if the expected page type is not found.
        """
        return self.goto(
            url, new_tab=True, timeout=timeout, expected_page=expected_page
        )

    def goto(
        self,
        url: str,
        new_tab: bool = False,
        timeout: Optional[float] = 15000,
        expected_page: str = "",
    ) -> Page:
        """
        Navigates to the specified URL, optionally in a new tab.

        Args:
            url (str): The URL to navigate to. If no protocol is specified, https:// will be added.
            new_tab (bool): Whether to open the URL in a new tab. Defaults to False.
            timeout (Optional[float]): The maximum time in milliseconds to wait for navigation.
                Defaults to 15000ms. Navigation will continue even if timeout occurs.
            expected_page (str): A description of the expected page type for verification.
                If provided, will verify the loaded page matches the description.
                Defaults to empty string (no verification).

        Returns:
            Page: The page object after navigation.

        Raises:
            IncorrectOutcomeError: If expected_page is provided and the loaded page
                doesn't match the expected description.
        """
        if not re.match("^\\w+://", url):
            url = f"https://{url}"
        active_page_manager = self._get_active_page_manager()
        if new_tab:
            active_page = active_page_manager.new_page()
        else:
            active_page = active_page_manager.get_active_page()
        try:
            logger.info(f"Going to {url}")
            active_page.playwright_page.goto(url, timeout=timeout)
        except TimeoutError:
            logger.debug("Timeout when loading page but continuing anyways.")
        except Exception as e:
            logger.debug(f"Exception when loading page but continuing anyways. {e}")
        if expected_page != "":
            try:
                prompt = f"We are checking if we have arrived on the expected type of page. If it is apparent that we have arrived on the wrong page, output an error. Here is the description: '{expected_page}'"
                active_page.ask(prompt, bool)
            except DendriteException as e:
                raise IncorrectOutcomeError(f"Incorrect navigation, reason: {e}")
        return active_page

    def scroll_to_bottom(
        self,
        timeout: float = 30000,
        scroll_increment: int = 1000,
        no_progress_limit: int = 3,
    ):
        """
        Scrolls to the bottom of the current page.

        Args:
            timeout (float): Maximum time in milliseconds to attempt scrolling.
                Defaults to 30000ms.
            scroll_increment (int): Number of pixels to scroll in each step.
                Defaults to 1000 pixels.
            no_progress_limit (int): Number of consecutive attempts with no progress
                before stopping. Defaults to 3 attempts.
        """
        active_page = self.get_active_page()
        active_page.scroll_to_bottom(
            timeout=timeout,
            scroll_increment=scroll_increment,
            no_progress_limit=no_progress_limit,
        )

    def _launch(self):
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
        self._playwright = sync_playwright().start()
        storage_states = []
        for domain in self._auth_domains:
            state = self._get_domain_storage_state(domain)
            if state:
                storage_states.append(state)
        browser = self._impl.start_browser(self._playwright, self._playwright_options)
        if storage_states:
            merged_state = self._merge_storage_states(storage_states)
            self.browser_context = browser.new_context(storage_state=merged_state)
        else:
            self.browser_context = (
                browser.contexts[0]
                if len(browser.contexts) > 0
                else browser.new_context()
            )
        self._active_page_manager = PageManager(self, self.browser_context)
        self._impl.configure_context(self)
        return (browser, self.browser_context, self._active_page_manager)

    def add_cookies(self, cookies):
        """
        Adds cookies to the current browser context.

        Args:
            cookies (List[Dict[str, Any]]): A list of cookie objects to be added.
                Each cookie should be a dictionary with standard cookie attributes
                (name, value, domain, etc.).

        Raises:
            DendriteException: If the browser context is not initialized.
        """
        if not self.browser_context:
            raise DendriteException("Browser context not initialized")
        self.browser_context.add_cookies(cookies)

    def close(self):
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
                for domain in self._auth_domains:
                    self.save_auth(domain)
                self._impl.stop_session()
                self.browser_context.close()
        except Error:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except (AttributeError, Exception):
            pass

    def _is_launched(self):
        """
        Checks whether the browser context has been launched.

        Returns:
            bool: True if the browser context is launched, False otherwise.
        """
        return self.browser_context is not None

    def _get_active_page_manager(self) -> PageManager:
        """
        Retrieves the active PageManager instance, launching the browser if necessary.

        Returns:
            PageManager: The active PageManager instance.

        Raises:
            Exception: If there is an issue launching the browser or retrieving the PageManager.
        """
        if not self._active_page_manager:
            (_, _, active_page_manager) = self._launch()
            return active_page_manager
        return self._active_page_manager

    def get_download(self, timeout: float) -> Download:
        """
        Retrieves the download event from the browser.

        Returns:
            Download: The download event.

        Raises:
            Exception: If there is an issue retrieving the download event.
        """
        active_page = self.get_active_page()
        pw_page = active_page.playwright_page
        return self._get_download(pw_page, timeout)

    def _get_download(self, pw_page: PlaywrightPage, timeout: float) -> Download:
        """
        Retrieves the download event from the browser.

        Returns:
            Download: The download event.

        Raises:
            Exception: If there is an issue retrieving the download event.
        """
        return self._download_handler.get_data(pw_page, timeout=timeout)

    def upload_files(
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
        page = self.get_active_page()
        file_chooser = self._get_filechooser(page.playwright_page, timeout)
        file_chooser.set_files(files)

    def _get_filechooser(
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
        return self._upload_handler.get_data(pw_page, timeout=timeout)

    def save_auth(self, url: str) -> None:
        """
        Save authentication state for a specific domain.

        This method captures and stores the current browser context's storage state
        (cookies and origin data) for the specified domain. The state can be later
        used to restore authentication.

        Args:
            url (str): URL or domain to save authentication for (e.g., "github.com"
                or "https://github.com"). The domain will be extracted from the URL.

        Raises:
            DendriteException: If the browser context is not initialized.
        """
        if not self.browser_context:
            raise DendriteException("Browser context not initialized")
        domain = get_domain_w_suffix(url)
        storage_state = self.browser_context.storage_state()
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
        self._config.storage_cache.set(
            {"domain": domain}, StorageState(**filtered_state)
        )

    def setup_auth(
        self,
        url: str,
        message: str = "Please log in to the website. Once done, press Enter to continue...",
    ) -> None:
        """
        Set up authentication for a specific URL by guiding the user through login.

        This method opens a browser window, navigates to the specified URL, waits for
        the user to complete the login process, and then saves the authentication state.

        Args:
            url (str): URL to navigate to for login
            message (str): Message to show while waiting for user to complete login.
                Defaults to standard login instruction message.
        """
        domain = get_domain_w_suffix(url)
        try:
            self._playwright = sync_playwright().start()
            browser = self._impl.start_browser(
                self._playwright, {**self._playwright_options, "headless": False}
            )
            self.browser_context = browser.new_context()
            self._active_page_manager = PageManager(self, self.browser_context)
            self.goto(url)
            print(message)
            input()
            self.save_auth(domain)
        finally:
            self.close()

    def _get_domain_storage_state(self, domain: str) -> Optional[StorageState]:
        """Get storage state for a specific domain"""
        return self._config.storage_cache.get({"domain": domain}, index=0)

    def _merge_storage_states(self, states: List[StorageState]) -> StorageState:
        """Merge multiple storage states into one"""
        merged = {"origins": [], "cookies": []}
        seen_origins = set()
        seen_cookies = set()
        for state in states:
            for origin in state.get("origins", []):
                origin_key = origin.get("origin", "")
                if origin_key not in seen_origins:
                    merged["origins"].append(origin)
                    seen_origins.add(origin_key)
            for cookie in state.get("cookies", []):
                cookie_key = (
                    f"{cookie.get('name')}:{cookie.get('domain')}:{cookie.get('path')}"
                )
                if cookie_key not in seen_cookies:
                    merged["cookies"].append(cookie)
                    seen_cookies.add(cookie_key)
        return StorageState(**merged)
