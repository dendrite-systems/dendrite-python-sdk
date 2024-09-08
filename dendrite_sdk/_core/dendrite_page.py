import asyncio
import pathlib
import time

from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Literal,
    Optional,
    Sequence,
    Union,
)

from bs4 import BeautifulSoup, Tag
from loguru import logger

from playwright.async_api import (
    Page,
    FrameLocator,
    Keyboard,
    Download,
    FilePayload,
)

from dendrite_sdk._core._js import GENERATE_DENDRITE_IDS_SCRIPT
from dendrite_sdk._core.dendrite_element import DendriteElement
from dendrite_sdk._core.mixin.ask import AskMixin
from dendrite_sdk._core.mixin.extract import ExtractionMixin
from dendrite_sdk._core.mixin.get_element import GetElementMixin
from dendrite_sdk._core.models.page_information import PageInformation


if TYPE_CHECKING:
    from dendrite_sdk._core._base_browser import BaseDendriteBrowser


from dendrite_sdk._core._managers.screenshot_manager import ScreenshotManager
from dendrite_sdk._exceptions.dendrite_exception import DendriteException


from dendrite_sdk._core._utils import (
    expand_iframes,
)


class DendritePage(ExtractionMixin, AskMixin, GetElementMixin):
    """
    Represents a page in the Dendrite browser environment.

    This class provides methods for interacting with and manipulating
    pages in the browser.
    """

    def __init__(self, page: Page, dendrite_browser: "BaseDendriteBrowser"):
        self.playwright_page = page
        self.screenshot_manager = ScreenshotManager()
        self.dendrite_browser = dendrite_browser
        self.browser_api_client = dendrite_browser._browser_api_client

    @property
    def url(self):
        """
        Get the current URL of the page.

        Returns:
            str: The current URL.
        """
        return self.playwright_page.url

    @property
    def keyboard(self) -> Keyboard:
        """
        Get the keyboard object for the page.

        Returns:
            Keyboard: The Playwright Keyboard object.
        """
        return self.playwright_page.keyboard

    async def goto(
        self,
        url: str,
        timeout: Optional[float] = 30000,
        wait_until: Optional[
            Literal["commit", "domcontentloaded", "load", "networkidle"]
        ] = "load",
    ) -> None:
        """
        Navigate to a URL.

        Args:
            url (str): The URL to navigate to.
            timeout (Optional[float]): Maximum navigation time in milliseconds.
            wait_until (Optional[Literal["commit", "domcontentloaded", "load", "networkidle"]]):
                When to consider navigation succeeded.
        """

        await self.playwright_page.goto(url, timeout=timeout, wait_until=wait_until)

    async def get_download(self, timeout: float = 30000) -> Download:
        """
        Retrieves the download event associated with.

        Args:
            timeout (float, optional): The maximum amount of time (in milliseconds) to wait for the download to complete. Defaults to 30.

        Returns:
            The downloaded file data.
        """
        return await self.dendrite_browser._get_download(timeout)

    def _get_context(self, element: Any) -> Union[Page, FrameLocator]:
        """
        Gets the correct context to be able to interact with an element on a different frame.

        e.g. if the element is inside an iframe,
        the context will be the frame locator for that iframe.

        Args:
            element (Any): The element to get the context for.

        Returns:
            Union[Page, FrameLocator]: The context for the element.
        """

        context = self.playwright_page

        if isinstance(element, Tag):
            full_path = element.get("iframe-path")
            if full_path:
                for path in full_path.split("|"):  # type: ignore
                    context = context.frame_locator(f"xpath=//iframe[@d-id='{path}']")

        return context

    async def scroll_to_bottom(self, timeout: float = 30000) -> None:
        """
        Scrolls to the bottom of the page continuously until the bottom is reached or a timeout occurs.

        This method scrolls the page in increments of 1000 pixels, checking the scroll position
        and resetting the timeout if progress is made. It stops scrolling once the bottom is reached
        or if the specified timeout is exceeded.

        Args:
            timeout (float, optional): The maximum amount of time (in milliseconds) to continue scrolling. Defaults to 30000.

        Returns:
            None
        """
        i = 0
        last_scroll_position = 0
        start_time = time.time()

        while True:
            current_scroll_position = await self.playwright_page.evaluate(
                "window.scrollY"
            )

            await self.playwright_page.evaluate(f"window.scrollTo(0, {i})")
            i += 1000

            if time.time() - start_time > timeout * 0.001:
                break

            if current_scroll_position - last_scroll_position > 1000:
                start_time = time.time()

            last_scroll_position = current_scroll_position

            await asyncio.sleep(0.1)

    async def _get_page_information(self) -> PageInformation:
        """
        Retrieves information about the current page, including the URL, raw HTML, and a screenshot.

        Returns:
            PageInformation: An object containing the page's URL, raw HTML, and a screenshot in base64 format.
        """
        soup = await self._get_soup()

        base64 = await self.screenshot_manager.take_full_page_screenshot(
            self.playwright_page
        )

        return PageInformation(
            url=self.playwright_page.url,
            raw_html=str(soup),
            screenshot_base64=base64,
        )

    async def _generate_dendrite_ids(self):
        """
        Attempts to generate Dendrite IDs in the DOM by executing a script.

        This method will attempt to generate the Dendrite IDs up to 3 times. If all attempts fail,
        an exception is raised.

        Raises:
            Exception: If the Dendrite IDs could not be generated after 3 attempts.
        """
        tries = 0
        while tries < 3:
            try:
                await self.playwright_page.evaluate(GENERATE_DENDRITE_IDS_SCRIPT)
                return
            except Exception as e:
                await self.playwright_page.wait_for_load_state(
                    state="load", timeout=3000
                )
                logger.debug(
                    f"Failed to generate dendrite IDs: {e}, attempt {tries+1}/3"
                )
                tries += 1

        raise Exception("Failed to add d-ids to DOM.")

    async def scroll_through_entire_page(self) -> None:
        """
        Scrolls through the entire page.

        Returns:
            None
        """
        await self.scroll_to_bottom()

    async def wait_for(
        self,
        prompt: str,
        timeout: float = 2000,
        max_retries: int = 5,
    ):
        """
        Waits for the condition specified in the prompt to become true by periodically checking the page content.

        This method attempts to retrieve the page information and evaluate whether the specified
        condition (provided in the prompt) is met. If the condition is not met after the specified
        number of retries, an exception is raised.

        Args:
            prompt (str): The prompt to determine the condition to wait for on the page.
            timeout (float, optional): The time (in milliseconds) to wait between each retry. Defaults to 2000.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 5.

        Returns:
            Any: The result of the condition evaluation if successful.

        Raises:
            DendriteException: If the condition is not met after the maximum number of retries.
        """

        num_attempts = 0
        await asyncio.sleep(
            0.2
        )  # HACK: Wait for page to load slightly when running first time
        while num_attempts < max_retries:
            num_attempts += 1
            try:
                start_time = time.time()
                page_information = await self._get_page_information()
                prompt = f"Prompt: '{prompt}'\n\nReturn a boolean that determines if the requested information or thing is available on the page."
                res = await self.ask(prompt, bool)
                elapsed_time = (
                    time.time() - start_time
                ) * 1000  # Convert to milliseconds

                if res:
                    return res

                if elapsed_time >= timeout:
                    # If the response took longer than the timeout, continue immediately
                    continue
                else:
                    # Otherwise, wait for the remaining time
                    await asyncio.sleep((timeout - elapsed_time) * 0.001)
            except Exception as e:
                logger.debug(f"Waited for page, but got this exception: {e}")
                continue

        page_information = await self._get_page_information()
        raise DendriteException(
            message=f"Retried {max_retries} times but failed to wait for the requested condition.",
            screenshot_base64=page_information.screenshot_base64,
        )

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
        Uploads files to the page using a file chooser.

        Args:
            files (Union[str, pathlib.Path, FilePayload, Sequence[Union[str, pathlib.Path]], Sequence[FilePayload]]): The file(s) to be uploaded.
                This can be a file path, a `FilePayload` object, or a sequence of file paths or `FilePayload` objects.
            timeout (float, optional): The maximum amount of time (in milliseconds) to wait for the file chooser to be ready. Defaults to 30.

        Returns:
            None
        """
        file_chooser = await self.dendrite_browser._get_filechooser(timeout)
        await file_chooser.set_files(files)

    async def get_content(self):
        """
        Retrieves the content of the current page.

        Returns:
            str: The HTML content of the current page.
        """
        return await self.playwright_page.content()

    async def _get_soup(self) -> BeautifulSoup:
        """
        Retrieves the page source as a BeautifulSoup object, with an option to exclude hidden elements.
        Generates Dendrite IDs in the DOM and expands iframes.

        Returns:
            BeautifulSoup: The parsed HTML of the current page.
        """
        await self._generate_dendrite_ids()

        page_source = await self.playwright_page.content()
        soup = BeautifulSoup(page_source, "lxml")
        await self._expand_iframes(soup)
        return soup

    async def _expand_iframes(self, page_source: BeautifulSoup):
        """
        Expands iframes in the given page source to make their content accessible.

        Args:
            page_source (BeautifulSoup): The parsed HTML content of the page.

        Returns:
            None
        """
        await expand_iframes(self.playwright_page, page_source)

    async def _get_all_elements_from_selector(self, selector: str):
        dendrite_elements: List[DendriteElement] = []
        soup = await self._get_soup()
        elements = soup.select(selector)

        for element in elements:
            frame = self._get_context(element)
            d_id = element.get("d-id", "")
            locator = frame.locator(f"xpath=//*[@d-id='{d_id}']")

            if not d_id:
                continue

            if isinstance(d_id, list):
                d_id = d_id[0]

            dendrite_elements.append(
                DendriteElement(
                    d_id,
                    locator,
                    self.dendrite_browser,
                )
            )

        if len(dendrite_elements) == 0:
            raise Exception(f"No elements found for selector '{selector}'")

        return dendrite_elements

    async def _dump_html(self, path: str) -> None:
        """
        Saves the current page's HTML content to a file.

        Args:
            path (str): The file path where the HTML content should be saved.

        Returns:
            None
        """

        with open(path, "w") as f:
            f.write(await self.playwright_page.content())
