import asyncio
import pathlib
import time

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    Union,
    overload,
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
from dendrite_sdk._core.models.page_information import PageInformation
from dendrite_sdk._core.models.response import DendriteElementsResponse
from dendrite_sdk._core._type_spec import (
    JsonSchema,
    PydanticModel,
    convert_to_type_spec,
    to_json_schema,
    TypeSpec,
)
from dendrite_sdk._core._utils import get_all_elements_from_selector


if TYPE_CHECKING:
    from dendrite_sdk._core._base_browser import BaseDendriteBrowser
from dendrite_sdk._api.dto.ask_page_dto import AskPageDTO
from dendrite_sdk._api.dto.scrape_page_dto import ScrapePageDTO
from dendrite_sdk._api.dto.get_elements_dto import GetElementsDTO
from dendrite_sdk._api.dto.scrape_page_dto import ScrapePageDTO
from dendrite_sdk._api.dto.try_run_script_dto import TryRunScriptDTO

from dendrite_sdk._core._managers.screenshot_manager import ScreenshotManager
from dendrite_sdk._exceptions.dendrite_exception import DendriteException


from dendrite_sdk._core._utils import (
    expand_iframes,
)
from dendrite_sdk._core.dendrite_element import DendriteElement


class DendritePage:
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
        Retrieves the downloaded file data.

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

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[bool],
        use_cache: bool = True,
    ) -> bool:
        """
        Extract data from a web page based on a prompt and return as a bool.

        Args:
            prompt (str): The prompt to guide the extraction.
            type_spec (Type[bool]): Specifies that the return type should be boolean.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.

        Returns:
            ScrapePageResponse[bool]: The extracted boolean data wrapped in a ScrapePageResponse.
        """

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[int],
        use_cache: bool = True,
    ) -> int:
        """
        Extract data from a web page based on a prompt and return as an integer.

        Args:
            prompt (str): The prompt to guide the extraction.
            type_spec (Type[int]): Specifies that the return type should be integer.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.

        Returns:
            ScrapePageResponse[int]: The extracted integer data wrapped in a ScrapePageResponse.
        """

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[float],
        use_cache: bool = True,
    ) -> float:
        """
        Extract data from a web page based on a prompt and return as a float.

        Args:
            prompt (str): The prompt to guide the extraction.
            type_spec (Type[float]): Specifies that the return type should be float.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.

        Returns:
            ScrapePageResponse[float]: The extracted float data wrapped in a ScrapePageResponse.
        """

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[str],
        use_cache: bool = True,
    ) -> str:
        """
        Extract data from a web page based on a prompt and return as a string.

        Args:
            prompt (str): The prompt to guide the extraction.
            type_spec (Type[str]): Specifies that the return type should be string.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.

        Returns:
            str: The extracted string data.
        """

    @overload
    async def extract(
        self,
        prompt: Optional[str],
        type_spec: Type[PydanticModel],
        use_cache: bool = True,
    ) -> PydanticModel:
        """
        Extract data from a web page and convert it to a Pydantic model.

        Args:
            prompt (Optional[str]): The prompt to guide the extraction. Can be None.
            type_spec (Type[PydanticModel]): The Pydantic model to convert the extracted data into.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.

        Returns:
            ScrapePageResponse[PydanticModel]: The extracted data as a Pydantic model wrapped in a ScrapePageResponse.
        """

    @overload
    async def extract(
        self,
        prompt: Optional[str],
        type_spec: JsonSchema,
        use_cache: bool = True,
    ) -> JsonSchema:
        """
        Extract data from a web page based on a prompt and validate it against the specified JSON schema.

        Args:
            prompt (Optional[str]): The prompt to guide the extraction. Can be None.
            type_spec (JsonSchema): The JSON schema to validate the extracted data against.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.

        Returns:
            ScrapePageResponse[JsonSchema]: The extracted data conforming to the JSON schema wrapped in a ScrapePageResponse.
        """
        ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: None = None,
        use_cache: bool = True,
    ) -> Any:
        """
        Extract data based on a prompt.

        Args:
            prompt (str): The prompt to guide the extraction.
            type_spec (None, optional): No type specification. Defaults to None.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.

        Returns:
            ScrapePageResponse[Any]: The extracted data of any type wrapped in a ScrapePageResponse.
        """

    async def extract(
        self,
        prompt: Optional[str],
        type_spec: Optional[TypeSpec] = None,
        use_cache: bool = True,
    ) -> TypeSpec:
        """
        Extract data from a web page based on a prompt and optional type specification.

        This function scrapes data from a web page using the provided prompt and type specification.
        It can handle various data types and schemas, including boolean, integer, float, Pydantic models,
        and JSON schemas.

        Args:
            prompt (Optional[str]): The prompt to guide the extraction. If None, an empty string is used.
            type_spec (Optional[TypeSpec], optional): The type specification for the extracted data. Defaults to None.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.

        Returns:
            ScrapePageResponse: The extracted data wrapped in a ScrapePageResponse object.

        Raises:
            Any exceptions that may occur during the scraping process.

        Note:
            This function uses overloading to provide type-specific behavior based on the `type_spec` argument.
        """

        json_schema = None
        if type_spec:
            json_schema = to_json_schema(type_spec)

        if prompt is None:
            prompt = ""

        page_information = await self._get_page_information()
        scrape_dto = ScrapePageDTO(
            page_information=page_information,
            llm_config=self.dendrite_browser.llm_config,
            prompt=prompt,
            return_data_json_schema=json_schema,
            use_screenshot=True,
            use_cache=use_cache,
        )
        res = await self.browser_api_client.scrape_page(scrape_dto)

        converted_res = res.return_data
        if type_spec is not None:
            converted_res = convert_to_type_spec(type_spec, res.return_data)

        res = converted_res

        return res

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

    @overload
    async def ask(self, prompt: str, type_spec: Type[str]) -> str:
        """
        Asks a question about the current page and expects a response of type `str`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[str]): The expected return type, which is `str`.

        Returns:
            AskPageResponse[str]: The response object containing the result of type `str`.
        """

    @overload
    async def ask(self, prompt: str, type_spec: Type[bool]) -> bool:
        """
        Asks a question about the current page and expects a responseof type `bool`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[bool]): The expected return type, which is `bool`.

        Returns:
            AskPageResponse[bool]: The response object containing the result of type `bool`.
        """

    @overload
    async def ask(self, prompt: str, type_spec: Type[int]) -> int:
        """
        Asks a question about the current page and expects a response of type `int`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[int]): The expected return type, which is `int`.

        Returns:
            AskPageResponse[int]: The response object containing the result of type `int`.
        """

    @overload
    async def ask(self, prompt: str, type_spec: Type[float]) -> float:
        """
        Asks a question about the current page and expects a response of type `float`.

         Args:
             prompt (str): The question or prompt to be asked.
             type_spec (Type[float]): The expected return type, which is `float`.

         Returns:
             AskPageResponse[float]: The response object containing the result of type `float`.
        """

    @overload
    async def ask(self, prompt: str, type_spec: Type[PydanticModel]) -> PydanticModel:
        """
        Asks a question about the current page and expects a response of a custom `PydanticModel`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[PydanticModel]): The expected return type, which is a `PydanticModel`.

        Returns:
            AskPageResponse[PydanticModel]: The response object containing the result of the specified Pydantic model type.
        """

    @overload
    async def ask(self, prompt: str, type_spec: Type[JsonSchema]) -> JsonSchema:
        """
        Asks a question about the current page and expects a response conforming to a `JsonSchema`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[JsonSchema]): The expected return type, which is a `JsonSchema`.

        Returns:
            AskPageResponse[JsonSchema]: The response object containing the result conforming to the specified JSON schema.
        """

    @overload
    async def ask(self, prompt: str, type_spec: None = None) -> JsonSchema:
        """
        Asks a question without specifying a type and expects a response conforming to a default `JsonSchema`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (None, optional): The expected return type, which is `None` by default.

        Returns:
            AskPageResponse[JsonSchema]: The response object containing the result conforming to the default JSON schema.
        """

    async def ask(
        self,
        prompt: str,
        type_spec: Optional[TypeSpec] = None,
    ) -> TypeSpec:
        """
        Asks a question and processes the response based on the specified type.

        This method sends a request to ask a question with the specified prompt and processes the response.
        If a type specification is provided, the response is converted to the specified type. In case of failure,
        a DendriteException is raised with relevant details.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Optional[TypeSpec], optional): The expected return type, which can be a type or a schema. Defaults to None.

        Returns:
            AskPageResponse[Any]: The response object containing the result, converted to the specified type if provided.

        Raises:
            DendriteException: If the request fails, the exception includes the failure message and a screenshot.
        """
        llm_config = self.dendrite_browser.llm_config
        page_information = await self._get_page_information()

        try:
            schema = None
            if type_spec:
                schema = to_json_schema(type_spec)

            dto = AskPageDTO(
                page_information=page_information,
                llm_config=llm_config,
                prompt=prompt,
                return_schema=schema,
            )
            res = await self.browser_api_client.ask_page(dto)

            converted_res = res.return_data
            if type_spec is not None:
                converted_res = convert_to_type_spec(type_spec, res.return_data)

            return converted_res
        except Exception as e:
            raise DendriteException(
                message=f"Failed to ask page: {e}",
                screenshot_base64=page_information.screenshot_base64,
            ) from e

    @overload
    async def get_elements(
        self,
        prompt_or_elements: str,
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 3000,
        context: str = "",
    ) -> List[DendriteElement]:
        """
        Retrieves a list of Dendrite elements based on a string prompt.

        Args:
            prompt_or_elements (str): The prompt describing the elements to be retrieved.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) between retries. Defaults to 3.
            context (str, optional): Additional context for the retrieval. Defaults to an empty string.

        Returns:
            List[DendriteElement]: A list of Dendrite elements found on the page.
        """

    @overload
    async def get_elements(
        self,
        prompt_or_elements: Dict[str, str],
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 3000,
        context: str = "",
    ) -> DendriteElementsResponse:
        """
        Retrieves Dendrite elements based on a dictionary.

        Args:
            prompt_or_elements (Dict[str, str]): A dictionary where keys are field names and values are prompts describing the elements to be retrieved.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) between retries. Defaults to 3.
            context (str, optional): Additional context for the retrieval. Defaults to an empty string.

        Returns:
            DendriteElementsResponse: A response object containing the retrieved elements with attributes matching the keys in the dict.
        """

    async def get_elements(
        self,
        prompt_or_elements: Union[str, Dict[str, str]],
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 3000,
        context: str = "",
    ) -> Union[List[DendriteElement], DendriteElementsResponse]:
        """
        Retrieves Dendrite elements based on either a string prompt or a dictionary of prompts.

        This method determines the type of the input (string or dictionary) and retrieves the appropriate elements.
        If the input is a string, it fetches a list of elements. If the input is a dictionary, it fetches elements for each key-value pair.

        Args:
            prompt_or_elements (Union[str, Dict[str, str]]): The prompt or dictionary of prompts for element retrieval.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) between retries. Defaults to 3.
            context (str, optional): Additional context for the retrieval. Defaults to an empty string.

        Returns:
            Union[List[DendriteElement], DendriteElementsResponse]: A list of elements or a response object containing the retrieved elements.

        Raises:
            ValueError: If the input is neither a string nor a dictionary.
        """

        if isinstance(prompt_or_elements, str):
            return await self._get_element(
                prompt_or_elements,
                only_one=False,
                use_cache=use_cache,
                max_retries=max_retries,
                timeout=timeout,
            )
        if isinstance(prompt_or_elements, dict):
            return await self.get_elements_from_dict(
                prompt_or_elements, context, use_cache, max_retries, timeout
            )

        raise ValueError("Prompt must be either a string prompt or a dictionary")

    async def get_elements_from_dict(
        self,
        prompt_dict: Dict[str, str],
        context: str,
        use_cache: bool,
        max_retries: int,
        timeout: int,
    ):
        """
        Retrieves Dendrite elements based on a dictionary of prompts, each associated with a context.

        This method sends a request for each prompt in the dictionary, adding context to each prompt, and retrieves the corresponding elements.

        Args:
            prompt_dict (Dict[str, str]): A dictionary where keys are field names and values are prompts describing the elements to be retrieved.
            context (str): Additional context to be added to each prompt.
            use_cache (bool): Whether to use cached results.
            max_retries (int): The maximum number of retry attempts.
            timeout (int): The timeout (in milliseconds) between retries.

        Returns:
            DendriteElementsResponse: A response object containing the retrieved elements mapped to their corresponding field names.
        """
        tasks = []
        for field_name, prompt in prompt_dict.items():
            full_prompt = prompt
            if context != "":
                full_prompt += f"\n\nHere is some extra context: {context}"
            task = self._get_element(
                full_prompt,
                only_one=True,
                use_cache=use_cache,
                max_retries=max_retries,
                timeout=timeout,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        elements_dict: Dict[str, DendriteElement] = {}
        for element, field_name in zip(results, prompt_dict.keys()):
            elements_dict[field_name] = element
        return DendriteElementsResponse(elements_dict)

    async def get_element(
        self,
        prompt: str,
        use_cache=True,
        max_retries=3,
        timeout=3000,
    ) -> DendriteElement:
        """
        Retrieves a single Dendrite element based on the provided prompt.

        Args:
            prompt (str): The prompt describing the element to be retrieved.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) between retries. Defaults to 3.

        Returns:
            DendriteElement: The retrieved element.
        """
        return await self._get_element(
            prompt,
            only_one=True,
            use_cache=use_cache,
            max_retries=max_retries,
            timeout=timeout,
        )

    @overload
    async def _get_element(
        self,
        prompt: str,
        only_one: Literal[True],
        use_cache: bool,
        max_retries,
        timeout,
    ) -> DendriteElement:
        """
        Retrieves a single Dendrite element based on the provided prompt.

        Args:
            prompt (str): The prompt describing the element to be retrieved.
            only_one (Literal[True]): Indicates that only one element should be retrieved.
            use_cache (bool): Whether to use cached results.
            max_retries: The maximum number of retry attempts.
            timeout: The timeout (in milliseconds) between retries.

        Returns:
            DendriteElement: The retrieved element.
        """

    @overload
    async def _get_element(
        self,
        prompt: str,
        only_one: Literal[False],
        use_cache: bool,
        max_retries,
        timeout,
    ) -> List[DendriteElement]:
        """
        Retrieves a list of Dendrite elements based on the provided prompt.

        Args:
            prompt (str): The prompt describing the elements to be retrieved.
            only_one (Literal[False]): Indicates that multiple elements should be retrieved.
            use_cache (bool): Whether to use cached results.
            max_retries: The maximum number of retry attempts.
            timeout: The timeout in seconds between retries.

        Returns:
            List[DendriteElement]: A list of retrieved elements.
        """

    async def _get_element(
        self, prompt: str, only_one: bool, use_cache: bool, max_retries, timeout
    ):
        """
        Retrieves Dendrite elements based on the provided prompt, either a single element or a list of elements.

        This method sends a request with the prompt and retrieves the elements based on the `only_one` flag.
        If no elements are found within the specified retries, an exception is raised.

        Args:
            prompt (str): The prompt describing the elements to be retrieved.
            only_one (bool): Whether to retrieve only one element or a list of elements.
            use_cache (bool): Whether to use cached results.
            max_retries: The maximum number of retry attempts.
            timeout: The timeout (in milliseconds) between retries.

        Returns:
            Union[DendriteElement, List[DendriteElement]]: The retrieved element or list of elements.

        Raises:
            DendriteException: If no suitable elements are found within the specified retries.
        """

        llm_config = self.dendrite_browser.llm_config
        for attempt in range(max_retries):
            is_last_attempt = attempt == max_retries - 1
            force_not_use_cache = is_last_attempt

            logger.info(
                f"Getting element for '{prompt}' | Attempt {attempt + 1}/{max_retries}"
            )

            page_information = await self._get_page_information()

            dto = GetElementsDTO(
                page_information=page_information,
                llm_config=llm_config,
                prompt=prompt,
                use_cache=use_cache and not force_not_use_cache,
                only_one=only_one,
            )
            selectors = await self.browser_api_client.get_interactions_selector(dto)
            logger.debug(f"Got selectors: {selectors}")
            if not selectors:
                raise DendriteException(
                    message="Could not find suitable elements on the page.",
                    screenshot_base64=page_information.screenshot_base64,
                )

            for selector in reversed(selectors["selectors"]):
                try:
                    dendrite_elements = await get_all_elements_from_selector(
                        self, selector
                    )
                    logger.info(f"Got working selector: {selector}")
                    return dendrite_elements[0] if only_one else dendrite_elements
                except Exception as e:
                    if is_last_attempt:
                        logger.warning(
                            f"Last attempt: Failed to get elements from selector with cache disabled",
                            exc_info=e,
                        )
                    else:
                        logger.warning(
                            f"Attempt {attempt + 1}: Failed to get elements from selector, trying again",
                            exc_info=e,
                        )

            if not is_last_attempt:
                await asyncio.sleep(timeout * 0.001)

        raise DendriteException(
            message="Could not find suitable elements on the page after all attempts.",
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
