from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, Union
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

from dendrite_sdk._api.dto.authenticate_dto import AuthenticateDTO
from dendrite_sdk._api.dto.upload_auth_session_dto import UploadAuthSessionDTO
from dendrite_sdk._api.response.interaction_response import InteractionResponse
from dendrite_sdk._common.event_sync import EventSync
from dendrite_sdk._core._managers.page_manager import (
    PageManager,
)

from dendrite_sdk._core.dendrite_page import DendritePage
from dendrite_sdk._common.constants import STEALTH_ARGS
from dendrite_sdk._core.models.authentication import (
    AuthSession,
)
from dendrite_sdk._core.models.llm_config import LLMConfig
from dendrite_sdk._api.browser_api_client import BrowserAPIClient
from dendrite_sdk._exceptions.dendrite_exception import (
    BrowserNotLaunchedError,
    DendriteException,
    IncorrectOutcomeError,
    MissingApiKeyError,
)


class BaseDendriteBrowser(ABC):
    """
    DendriteBrowser is a class that manages a browser instance using Playwright, allowing
    interactions with web pages using natural language.

    This class handles initialization with API keys for Dendrite, OpenAI, and Anthropic, manages browser
    contexts, and provides methods for navigation, authentication, and other browser-related tasks.

    Attributes:
        id (UUID): The unique identifier for the DendriteBrowser instance.
        auth_data (Optional[AuthSession]): The authentication session data for the browser.
        dendrite_api_key (str): The API key for Dendrite, used for interactions with the Dendrite API.
        playwright_options (dict): Options for configuring the Playwright browser instance.
        playwright (Optional[Playwright]): The Playwright instance managing the browser.
        browser_context (Optional[BrowserContext]): The current browser context, which may include cookies and other session data.
        active_page_manager (Optional[PageManager]): The manager responsible for handling active pages within the browser context.
        user_id (Optional[str]): The user ID associated with the browser session.
        browser_api_client (BrowserAPIClient): The API client used for communicating with the Dendrite API.
        llm_config (LLMConfig): The configuration for the language models, including API keys for OpenAI and Anthropic.

    Raises:
        Exception: If any of the required API keys (Dendrite, OpenAI, Anthropic) are not provided or found in the environment variables.
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        dendrite_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        playwright_options: Any = {
            "headless": False,
            "args": STEALTH_ARGS,
        },
    ):
        """
        Initializes the DendriteBrowser with API keys and Playwright options.

        Args:
            id (Optional[str]): An optional ID for the browser instance. If not provided, a UUID is generated.
            openai_api_key (Optional[str], optional): The OpenAI API key. If not provided, it's fetched from the environment variables.
            dendrite_api_key (Optional[str], optional): The Dendrite API key. If not provided, it's fetched from the environment variables.
            anthropic_api_key (Optional[str], optional): The Anthropic API key. If not provided, it's fetched from the environment variables.
            playwright_options (Any, optional): Options for configuring Playwright. Defaults to running in non-headless mode with stealth arguments.

        Raises:
            Exception: If any of the required API keys (Dendrite, OpenAI, Anthropic) are not provided or found in the environment variables.
        """

        if not dendrite_api_key or dendrite_api_key == "":
            dendrite_api_key = os.environ.get("DENDRITE_API_KEY", "")
            if not dendrite_api_key or dendrite_api_key == "":
                raise MissingApiKeyError(
                    "Dendrite API key is required to use DendriteBrowser"
                )

        if not anthropic_api_key or anthropic_api_key == "":
            anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            if anthropic_api_key == "":
                raise MissingApiKeyError(
                    "Anthropic API key is required to use DendriteBrowser"
                )

        if not openai_api_key or openai_api_key == "":
            openai_api_key = os.environ.get("OPENAI_API_KEY", "")
            if not openai_api_key or openai_api_key == "":
                raise MissingApiKeyError(
                    "OpenAI API key is required to use DendriteBrowser"
                )

        self._id = uuid4().hex
        self._auth_data: Optional[AuthSession] = None
        self._dendrite_api_key = dendrite_api_key
        self._playwright_options = playwright_options
        self._active_page_manager: Optional[PageManager] = None
        self._user_id: Optional[str] = None
        self._browser_api_client = BrowserAPIClient(dendrite_api_key, self._id)
        self.playwright: Optional[Playwright] = None
        self.browser_context: Optional[BrowserContext] = None
        self._upload_handler = EventSync[FileChooser]()
        self._download_handler = EventSync[Download]()
        self.closed = False

        llm_config = LLMConfig(
            openai_api_key=openai_api_key, anthropic_api_key=anthropic_api_key
        )
        self.llm_config = llm_config

    @property
    def pages(self) -> List[DendritePage]:
        """
        Retrieves the list of active pages managed by the PageManager.

        Returns:
            List[DendritePage]: The list of active pages.
        """
        if self._active_page_manager:
            return self._active_page_manager.pages
        else:
            raise BrowserNotLaunchedError()

    async def __aenter__(self):
        # Launch the browser and return the instance
        await self._launch()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Ensure cleanup is handled
        await self.close()

    async def get_active_page(self) -> DendritePage:
        """
        Retrieves the currently active page managed by the PageManager.

        Returns:
            DendritePage: The active page object.

        Raises:
            Exception: If there is an issue retrieving the active page.
        """

        active_page_manager = await self._get_active_page_manager()
        return await active_page_manager.get_active_page()

    async def goto(
        self,
        url: str,
        new_page: bool = False,
        timeout: Optional[float] = 15000,
        authenticate: bool = False,
        expected_page: str = "",
    ) -> DendritePage:
        """
        Navigates to the specified URL, optionally in a new tab

        Args:
            url (str): The URL to navigate to.
            new_page (bool, optional): Whether to open the URL in a new page. Defaults to False.
            timeout (Optional[float], optional): The maximum time (in milliseconds) to wait for the page to load. Defaults to 15000.
            authenticate (bool, optional): Whether to authenticate before navigating to the URL. Defaults to False.
            expected_page (str, optional): A description of the expected page type for verification. Defaults to an empty string.

        Returns:
            DendritePage: The page object after navigation.

        Raises:
            Exception: If there is an error during navigation or if the expected page type is not found.
        """

        if authenticate:
            await self.authenticate(url)

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
        os.environ["PW_TEST_SCREENSHOT_NO_FONTS_READY"] = "1"
        self._playwright = await async_playwright().start()
        browser = await self._playwright.chromium.launch(**self._playwright_options)

        if self._auth_data:
            self.browser_context = await browser.new_context(
                storage_state=self._auth_data.to_storage_state(),
                user_agent=self._auth_data.user_agent,
            )
        else:
            self.browser_context = await browser.new_context()

        await self.browser_context.tracing.start(
            screenshots=True, snapshots=True, sources=True
        )
        self._active_page_manager = PageManager(self, self.browser_context)
        return browser, self.browser_context, self._active_page_manager

    async def authenticate(self, domains: Union[str, list[str]]):
        """
        Authenticates the browser for the specified domains.

        Args:
            domains (Union[str, list[str]]): A domain or list of domains to authenticate.

        Returns:
            None

        Raises:
            Exception: If authentication fails.
        """
        dto = AuthenticateDTO(domains=domains)
        auth_session: AuthSession = await self._browser_api_client.authenticate(dto)
        self._auth_data = auth_session

    async def new_page(self) -> DendritePage:
        """
        Opens a new page in the browser.

        Returns:
            DendritePage: The newly opened page.

        Raises:
            Exception: If there is an issue opening a new page.
        """
        active_page_manager = await self._get_active_page_manager()
        return await active_page_manager.new_page()

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
            if self._auth_data:
                storage_state = await self.browser_context.storage_state()
                dto = UploadAuthSessionDTO(
                    auth_data=self._auth_data, storage_state=storage_state
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
    async def _get_download(self, timeout: float) -> Download:
        """
        Retrieves the download event from the browser.

        Returns:
            Download: The download event.

        Raises:
            Exception: If there is an issue retrieving the download event.
        """
        pass

    async def _get_filechooser(self, timeout: float = 30000) -> FileChooser:
        """
        Uploads files to the browser.

        Args:
            timeout (float): The maximum time to wait for the file chooser dialog. Defaults to 30000 milliseconds.

        Returns:
            FileChooser: The file chooser dialog.

        Raises:
            Exception: If there is an issue uploading files.
        """
        return await self._upload_handler.get_data(timeout=timeout)

    async def fill_fields(self, fields: Dict[str, Any]):
        """
        Fills multiple fields on the active page with the provided values.

        This method iterates through the given dictionary of fields and their corresponding values,
        making a separate fill request for each key-value pair.

        Args:
            fields (Dict[str, Any]): A dictionary where each key is a field identifier (e.g., a prompt or selector)
                                     and each value is the content to fill in that field.

        Returns:
            None

        Note:
            This method will make multiple fill requests, one for each key in the 'fields' dictionary.
        """
        active_page = await self.get_active_page()
        return await active_page.fill_fields(fields)

    async def click(
        self,
        prompt: str,
        expected_outcome: Optional[str] = None,
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 2000,
        force: bool = False,
        *args,
        **kwargs,
    ) -> InteractionResponse:
        """
        Clicks an element on the active page based on the provided prompt.

        Args:
            prompt (str): The prompt describing the element to be clicked.
            expected_outcome (Optional[str]): The expected outcome of the click action.
            use_cache (bool, optional): Whether to use cached results for element retrieval. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts for element retrieval. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) for the click operation. Defaults to 2000.
            force (bool, optional): Whether to force the click operation. Defaults to False.
            *args: Additional positional arguments for the click operation.
            **kwargs: Additional keyword arguments for the click operation.

        Returns:
            InteractionResponse: The response from the interaction.

        Raises:
            DendriteException: If no suitable element is found or if the click operation fails.
        """
        active_page = await self.get_active_page()
        return await active_page.click(
            prompt,
            expected_outcome=expected_outcome,
            use_cache=use_cache,
            max_retries=max_retries,
            timeout=timeout,
            force=force,
            *args,
            **kwargs,
        )

    async def fill(
        self,
        prompt: str,
        value: str,
        expected_outcome: Optional[str] = None,
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 2000,
        *args,
        **kwargs,
    ) -> InteractionResponse:
        """
        Fills an element on the active page with the provided value based on the given prompt.

        Args:
            prompt (str): The prompt describing the element to be filled.
            value (str): The value to fill the element with.
            expected_outcome (Optional[str]): The expected outcome of the fill action.
            use_cache (bool, optional): Whether to use cached results for element retrieval. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts for element retrieval. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) for the fill operation. Defaults to 2000.
            *args: Additional positional arguments for the fill operation.
            **kwargs: Additional keyword arguments for the fill operation.

        Returns:
            InteractionResponse: The response from the interaction.

        Raises:
            DendriteException: If no suitable element is found or if the fill operation fails.
        """
        active_page = await self.get_active_page()
        return await active_page.fill(
            prompt,
            value,
            expected_outcome=expected_outcome,
            use_cache=use_cache,
            max_retries=max_retries,
            timeout=timeout,
            *args,
            **kwargs,
        )

    async def extract(
        self,
        prompt: str,
        expected_type: Any,
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 2000,
    ) -> Any:
        """
        Extracts information from the active page based on the provided prompt.

        Args:
            prompt (str): The prompt describing the information to be extracted.
            expected_type (Any): The expected type of the extracted information.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) for the extraction operation. Defaults to 2000.

        Returns:
            Any: The extracted information of the specified type.

        Raises:
            DendriteException: If the extraction fails or the result doesn't match the expected type.
        """
        active_page = await self.get_active_page()
        return await active_page.extract(
            prompt,
            expected_type,
            use_cache=use_cache,
            max_retries=max_retries,
            timeout=timeout,
        )

    async def ask(
        self,
        prompt: str,
        expected_type: Any,
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 2000,
    ) -> Any:
        """
        Asks a question about the active page based on the provided prompt.

        Args:
            prompt (str): The prompt or question to be asked about the page.
            expected_type (Any): The expected type of the answer.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) for the ask operation. Defaults to 2000.

        Returns:
            Any: The answer to the question of the specified type.

        Raises:
            DendriteException: If the ask operation fails or the result doesn't match the expected type.
        """
        active_page = await self.get_active_page()
        return await active_page.ask(
            prompt,
            expected_type,
            use_cache=use_cache,
            max_retries=max_retries,
            timeout=timeout,
        )

    async def wait_for(self, prompt: str, timeout: float = 2000, max_retries: int = 5):
        """
        Waits for a condition specified by the prompt to become true on the active page.

        Args:
            prompt (str): The prompt describing the condition to wait for.
            timeout (float, optional): The time (in milliseconds) to wait between each retry. Defaults to 2000.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 5.

        Returns:
            Any: The result of the condition evaluation if successful.

        Raises:
            PageConditionNotMet: If the condition is not met after the maximum number of retries.
        """
        active_page = await self.get_active_page()
        return await active_page.wait_for(
            prompt, timeout=timeout, max_retries=max_retries
        )

    async def press_keyboard(self, key: Union[str, Literal["Enter"]]) -> Any:
        """
        Presses a keyboard key on the active page.

        Args:
            key (Union[str, Literal["Enter"]]): The key to be pressed.

        Returns:
            Any: The result of the key press operation.

        Raises:
            DendriteException: If the key press operation fails.
        """
        active_page = await self.get_active_page()
        return await active_page.keyboard.press(key)
