from playwright.async_api import FileChooser, Download, Page
from dendrite_sdk.async_api._core._base_browser import BaseAsyncDendrite


class AsyncDendrite(BaseAsyncDendrite):
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
        llm_config (LLMConfig): The configuration for the language models, including API keys for OpenAI and Anthropic.

    Raises:
        Exception: If any of the required API keys (Dendrite, OpenAI, Anthropic) are not provided or found in the environment variables.
    """

    async def _get_download(self, pw_page: Page, timeout: float = 30000) -> Download:
        """
        Retrieves the download event from the browser.

        Args:
            timeout (float): The maximum time (in milliseconds) to wait for the download event.
        Returns:
            Download: The download event.

        Raises:
            Exception: If there is an issue retrieving the download event.
        """
        return await self._download_handler.get_data(pw_page, timeout)

    async def _get_filechooser(
        self, pw_page: Page, timeout: float = 30000
    ) -> FileChooser:
        """
        Uploads files to the browser.

        Args:
            timeout (float): The maximum time (in milliseconds) to wait for the file chooser dialog.
        Returns:
            FileChooser: The file chooser dialog.

        Raises:
            Exception: If there is an issue uploading files.
        """
        return await self._upload_handler.get_data(pw_page, timeout)
