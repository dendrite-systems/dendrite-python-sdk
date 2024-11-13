from abc import ABC, abstractmethod
import pathlib
import re
from typing import Any, List, Literal, Optional, Sequence, Union
from uuid import uuid4
import os
from loguru import logger
from playwright.sync_api import (
    sync_playwright,
    Playwright,
    BrowserContext,
    FileChooser,
    Download,
    Error,
    FilePayload,
)
from dendrite.browser.sync_api._api.dto.authenticate_dto import AuthenticateDTO
from dendrite.browser.sync_api._api.dto.upload_auth_session_dto import UploadAuthSessionDTO
from dendrite.browser.sync_api._common.event_sync import EventSync
from dendrite.browser.sync_api._core._impl_browser import ImplBrowser
from dendrite.browser.sync_api._core._impl_mapping import get_impl
from dendrite.browser.sync_api._core._managers.page_manager import PageManager
from dendrite.browser.sync_api._core._type_spec import PlaywrightPage
from dendrite.browser.sync_api._core.dendrite_page import Page
from dendrite.browser.sync_api._common.constants import STEALTH_ARGS
from dendrite.browser.sync_api._core.mixin.ask import AskMixin
from dendrite.browser.sync_api._core.mixin.click import ClickMixin
from dendrite.browser.sync_api._core.mixin.extract import ExtractionMixin
from dendrite.browser.sync_api._core.mixin.fill_fields import FillFieldsMixin
from dendrite.browser.sync_api._core.mixin.get_element import GetElementMixin
from dendrite.browser.sync_api._core.mixin.keyboard import KeyboardMixin
from dendrite.browser.sync_api._core.mixin.screenshot import ScreenshotMixin
from dendrite.browser.sync_api._core.mixin.wait_for import WaitForMixin
from dendrite.browser.sync_api._core.mixin.markdown import MarkdownMixin
from dendrite.browser.sync_api._core.models.authentication import AuthSession
from dendrite.browser.sync_api._core.models.api_config import APIConfig
from dendrite.browser.sync_api._api.browser_api_client import BrowserAPIClient
from dendrite.browser._common._exceptions.dendrite_exception import (
    BrowserNotLaunchedError,
    DendriteException,
    IncorrectOutcomeError,
)
from dendrite.browser.remote import Providers


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

    This class handles initialization with API keys for Dendrite, OpenAI, and Anthropic, manages browser
    contexts, and provides methods for navigation, authentication, and other browser-related tasks.

    Attributes:
        id (UUID): The unique identifier for the Dendrite instance.
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
        auth: Optional[Union[str, List[str]]] = None,
        dendrite_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        playwright_options: Any = {"headless": False, "args": STEALTH_ARGS},
        remote_config: Optional[Providers] = None,
    ):
        """
        Initializes Dendrite with API keys and Playwright options.

        Args:
            auth (Optional[Union[str, List[str]]]): The domains on which the browser should try and authenticate.
            dendrite_api_key (Optional[str]): The Dendrite API key. If not provided, it's fetched from the environment variables.
            openai_api_key (Optional[str]): Your own OpenAI API key, provide it, along with other custom API keys, if you wish to use Dendrite without paying for a license.
            anthropic_api_key (Optional[str]): The own Anthropic API key, provide it, along with other custom API keys, if you wish to use Dendrite without paying for a license.
            playwright_options (Any): Options for configuring Playwright. Defaults to running in non-headless mode with stealth arguments.

        Raises:
            MissingApiKeyError: If the Dendrite API key is not provided or found in the environment variables.
        """
        api_config = APIConfig(
            dendrite_api_key=dendrite_api_key or os.environ.get("DENDRITE_API_KEY"),
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
        )
        self._impl = self._get_impl(remote_config)
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

    def _get_browser_api_client(self) -> BrowserAPIClient:
        return self._browser_api_client

    def _get_dendrite_browser(self) -> "Dendrite":
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_impl(self, remote_provider: Optional[Providers]) -> ImplBrowser:
        return get_impl(remote_provider)

    def _get_auth_session(self, domains: Union[str, list[str]]):
        dto = AuthenticateDTO(domains=domains)
        auth_session: AuthSession = self._browser_api_client.authenticate(dto)
        return auth_session

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
        Navigates to the specified URL, optionally in a new tab

        Args:
            url (str): The URL to navigate to.
            new_tab (bool, optional): Whether to open the URL in a new tab. Defaults to False.
            timeout (Optional[float], optional): The maximum time (in milliseconds) to wait for the page to load. Defaults to 15000.
            expected_page (str, optional): A description of the expected page type for verification. Defaults to an empty string.

        Returns:
            Page: The page object after navigation.

        Raises:
            Exception: If there is an error during navigation or if the expected page type is not found.
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

        Returns:
            None
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
        browser = self._impl.start_browser(self._playwright, self._playwright_options)
        if self._auth:
            auth_session = self._get_auth_session(self._auth)
            self.browser_context = browser.new_context(
                storage_state=auth_session.to_storage_state(),
                user_agent=auth_session.user_agent,
            )
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
            cookies (List[Dict[str, Any]]): A list of cookies to be added to the browser context.

        Raises:
            Exception: If the browser context is not initialized.
        """
        if not self.browser_context:
            raise DendriteException("Browser context not initialized")
        self.browser_context.add_cookies(cookies)

    def close(self):
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
        try:
            if self.browser_context:
                if self._auth:
                    auth_session = self._get_auth_session(self._auth)
                    storage_state = self.browser_context.storage_state()
                    dto = UploadAuthSessionDTO(
                        auth_data=auth_session, storage_state=storage_state
                    )
                    self._browser_api_client.upload_auth_session(dto)
                self._impl.stop_session()
                self.browser_context.close()
        except Error:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except AttributeError:
            pass
        except Exception:
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
