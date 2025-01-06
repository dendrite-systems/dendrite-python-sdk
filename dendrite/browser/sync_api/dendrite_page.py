import time
import pathlib
import re
import time
from typing import TYPE_CHECKING, Any, List, Literal, Optional, Sequence, Union
from bs4 import BeautifulSoup, Tag
from loguru import logger
from playwright.sync_api import Download, FilePayload, FrameLocator, Keyboard
from dendrite.logic import LogicEngine
from dendrite.models.page_information import PageInformation
from .dendrite_element import Element
from .js import GENERATE_DENDRITE_IDS_SCRIPT
from .mixin.ask import AskMixin
from .mixin.click import ClickMixin
from .mixin.extract import ExtractionMixin
from .mixin.fill_fields import FillFieldsMixin
from .mixin.get_element import GetElementMixin
from .mixin.keyboard import KeyboardMixin
from .mixin.markdown import MarkdownMixin
from .mixin.wait_for import WaitForMixin
from .types import PlaywrightPage

if TYPE_CHECKING:
    from .dendrite_browser import Dendrite
from dendrite.browser._common._exceptions.dendrite_exception import DendriteException
from ._utils import expand_iframes
from .manager.screenshot_manager import ScreenshotManager


class Page(
    MarkdownMixin,
    ExtractionMixin,
    WaitForMixin,
    AskMixin,
    FillFieldsMixin,
    ClickMixin,
    KeyboardMixin,
    GetElementMixin,
):
    """
    Represents a page in the Dendrite browser environment.

    This class provides methods for interacting with and manipulating
    pages in the browser.
    """

    def __init__(
        self,
        page: PlaywrightPage,
        dendrite_browser: "Dendrite",
        browser_api_client: LogicEngine,
    ):
        self.playwright_page = page
        self.screenshot_manager = ScreenshotManager(page)
        self._browser_api_client = browser_api_client
        self._last_main_frame_url = page.url
        self._last_frame_navigated_timestamp = time.time()
        self._dendrite_browser = dendrite_browser
        self.playwright_page.on("framenavigated", self._on_frame_navigated)

    def _on_frame_navigated(self, frame):
        if frame is self.playwright_page.main_frame:
            self._last_main_frame_url = frame.url
            self._last_frame_navigated_timestamp = time.time()

    @property
    def dendrite_browser(self) -> "Dendrite":
        return self._dendrite_browser

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

    def _get_page(self) -> "Page":
        return self

    @property
    def logic_engine(self) -> LogicEngine:
        return self._browser_api_client

    def goto(
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
            url (str): The URL to navigate to. If no protocol is specified, 'https://' will be added.
            timeout (Optional[float]): Maximum navigation time in milliseconds.
            wait_until (Optional[Literal["commit", "domcontentloaded", "load", "networkidle"]]):
                When to consider navigation succeeded.
        """
        if not re.match("^\\w+://", url):
            url = f"https://{url}"
        self.playwright_page.goto(url, timeout=timeout, wait_until=wait_until)

    def get_download(self, timeout: float = 30000) -> Download:
        """
        Retrieves the download event associated with.

        Args:
            timeout (float, optional): The maximum amount of time (in milliseconds) to wait for the download to complete. Defaults to 30.

        Returns:
            The downloaded file data.
        """
        return self.dendrite_browser._get_download(self.playwright_page, timeout)

    def _get_context(self, element: Any) -> Union[PlaywrightPage, FrameLocator]:
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
                full_path = full_path[0] if isinstance(full_path, list) else full_path
                for path in full_path.split("|"):
                    context = context.frame_locator(f"xpath=//iframe[@d-id='{path}']")
        return context

    def scroll_to_bottom(
        self,
        timeout: float = 30000,
        scroll_increment: int = 1000,
        no_progress_limit: int = 3,
    ) -> None:
        """
        Scrolls to the bottom of the page until no more progress is made or a timeout occurs.

        Args:
            timeout (float, optional): The maximum amount of time (in milliseconds) to continue scrolling. Defaults to 30000.
            scroll_increment (int, optional): The number of pixels to scroll in each step. Defaults to 1000.
            no_progress_limit (int, optional): The number of consecutive attempts with no progress before stopping. Defaults to 3.

        Returns:
            None
        """
        start_time = time.time()
        last_scroll_position = 0
        no_progress_count = 0
        while True:
            current_scroll_position = self.playwright_page.evaluate("window.scrollY")
            scroll_height = self.playwright_page.evaluate("document.body.scrollHeight")
            self.playwright_page.evaluate(
                f"window.scrollTo(0, {current_scroll_position + scroll_increment})"
            )
            if (
                self.playwright_page.viewport_size
                and current_scroll_position
                + self.playwright_page.viewport_size["height"]
                >= scroll_height
            ):
                break
            if current_scroll_position > last_scroll_position:
                no_progress_count = 0
            else:
                no_progress_count += 1
            if no_progress_count >= no_progress_limit:
                break
            if time.time() - start_time > timeout * 0.001:
                break
            last_scroll_position = current_scroll_position
            time.sleep(0.1)

    def close(self) -> None:
        """
        Closes the current page.

        Returns:
            None
        """
        self.playwright_page.close()

    def get_page_information(self, include_screenshot: bool = True) -> PageInformation:
        """
        Retrieves information about the current page, including the URL, raw HTML, and a screenshot.

        Returns:
            PageInformation: An object containing the page's URL, raw HTML, and a screenshot in base64 format.
        """
        if include_screenshot:
            base64 = self.screenshot_manager.take_full_page_screenshot()
        else:
            base64 = "No screenshot available"
        soup = self._get_soup()
        return PageInformation(
            url=self.playwright_page.url,
            raw_html=str(soup),
            screenshot_base64=base64,
            time_since_frame_navigated=self.get_time_since_last_frame_navigated(),
        )

    def _generate_dendrite_ids(self):
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
                self.playwright_page.evaluate(GENERATE_DENDRITE_IDS_SCRIPT)
                return
            except Exception as e:
                self.playwright_page.wait_for_load_state(state="load", timeout=3000)
                logger.exception(
                    f"Failed to generate dendrite IDs: {e}, attempt {tries + 1}/3"
                )
                tries += 1
        raise DendriteException("Failed to add d-ids to DOM.")

    def scroll_through_entire_page(self) -> None:
        """
        Scrolls through the entire page.

        Returns:
            None
        """
        self.scroll_to_bottom()

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
        Uploads files to the page using a file chooser.

        Args:
            files (Union[str, pathlib.Path, FilePayload, Sequence[Union[str, pathlib.Path]], Sequence[FilePayload]]): The file(s) to be uploaded.
                This can be a file path, a `FilePayload` object, or a sequence of file paths or `FilePayload` objects.
            timeout (float, optional): The maximum amount of time (in milliseconds) to wait for the file chooser to be ready. Defaults to 30.

        Returns:
            None
        """
        file_chooser = self.dendrite_browser._get_filechooser(
            self.playwright_page, timeout
        )
        file_chooser.set_files(files)

    def get_content(self):
        """
        Retrieves the content of the current page.

        Returns:
            str: The HTML content of the current page.
        """
        return self.playwright_page.content()

    def _get_soup(self) -> BeautifulSoup:
        """
        Retrieves the page source as a BeautifulSoup object, with an option to exclude hidden elements.
        Generates Dendrite IDs in the DOM and expands iframes.

        Returns:
            BeautifulSoup: The parsed HTML of the current page.
        """
        self._generate_dendrite_ids()
        page_source = self.playwright_page.content()
        soup = BeautifulSoup(page_source, "lxml")
        self._expand_iframes(soup)
        self._previous_soup = soup
        return soup

    def _get_previous_soup(self) -> BeautifulSoup:
        """
        Retrieves the page source generated by the latest _get_soup() call as a Beautiful soup object. If it hasn't been called yet, it will call it.
        """
        if self._previous_soup is None:
            return self._get_soup()
        return self._previous_soup

    def _expand_iframes(self, page_source: BeautifulSoup):
        """
        Expands iframes in the given page source to make their content accessible.

        Args:
            page_source (BeautifulSoup): The parsed HTML content of the page.

        Returns:
            None
        """
        expand_iframes(self.playwright_page, page_source)

    def _get_all_elements_from_selector(self, selector: str) -> List[Element]:
        dendrite_elements: List[Element] = []
        soup = self._get_soup()
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
                Element(d_id, locator, self.dendrite_browser, self._browser_api_client)
            )
        return dendrite_elements

    def _dump_html(self, path: str) -> None:
        """
        Saves the current page's HTML content to a file.

        Args:
            path (str): The file path where the HTML content should be saved.

        Returns:
            None
        """
        with open(path, "w") as f:
            f.write(self.playwright_page.content())

    def get_time_since_last_frame_navigated(self) -> float:
        """
        Get the time elapsed since the last URL change.

        Returns:
            float: The number of seconds elapsed since the last URL change.
        """
        return time.time() - self._last_frame_navigated_timestamp

    def check_if_renavigated(self, initial_url: str, wait_time: float = 0.1) -> bool:
        """
        Waits for a short period and checks if a main frame navigation has occurred.

        Args:
            wait_time (float): The time to wait in seconds. Defaults to 0.1 seconds.

        Returns:
            bool: True if a main frame navigation occurred, False otherwise.
        """
        time.sleep(wait_time)
        return self._last_main_frame_url != initial_url
