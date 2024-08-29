from __future__ import annotations
import asyncio
import time
from playwright.async_api import Page, Locator
from bs4 import BeautifulSoup, Tag
import pathlib
import time

from typing import TYPE_CHECKING, Any, List, Optional, Type
from dendrite_python_sdk.dendrite_browser.SelectorManager import SelectorManager
from dendrite_python_sdk.dto.GetElementsDTO import GetElementsDTO

from dendrite_python_sdk.dto.ScrapePageDTO import ScrapePageDTO
from dendrite_python_sdk.dto.TryRunScriptDTO import TryRunScriptDTO
from dendrite_python_sdk.exceptions.DendriteException import DendriteException
from dendrite_python_sdk.responses.ScrapePageResponse import ScrapePageResponse

if TYPE_CHECKING:
    from dendrite_python_sdk import DendriteBrowser

from dendrite_python_sdk.dendrite_browser.ScreenshotManager import ScreenshotManager
from dendrite_python_sdk.models.PageInformation import PageInformation


from playwright.async_api import (
    Page,
    Locator,
    FrameLocator,
    Keyboard,
    FileChooser,
    Download,
    FilePayload,
)
from bs4 import BeautifulSoup, Tag
from loguru import logger

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    Sequence,
    Type,
    Union,
    overload,
)


from dendrite_python_sdk.dendrite_browser.scripts import GENERATE_DENDRITE_IDS_SCRIPT
from dendrite_python_sdk.dendrite_browser.type_spec import (
    JsonSchema,
    PydanticModel,
    convert_to_type_spec,
    to_json_schema,
    TypeSpec,
)


from dendrite_python_sdk.dto.AskPageDTO import AskPageDTO
from dendrite_python_sdk.dto.ScrapePageDTO import ScrapePageDTO
from dendrite_python_sdk.dto.TryRunScriptDTO import TryRunScriptDTO
from dendrite_python_sdk.exceptions.DendriteException import DendriteException
from dendrite_python_sdk.responses.AskPageResponse import AskPageResponse
from dendrite_python_sdk.responses.ScrapePageResponse import ScrapePageResponse

if TYPE_CHECKING:
    from dendrite_python_sdk.dendrite_browser.DendriteBrowser import DendriteBrowser

from dendrite_python_sdk.dendrite_browser.ScreenshotManager import ScreenshotManager
from dendrite_python_sdk.dendrite_browser.utils import (
    expand_iframes,
)
from dendrite_python_sdk.models.PageInformation import PageInformation
from dendrite_python_sdk.dendrite_browser.DendriteElement import DendriteElement


class DendriteElementsResponse:
    _data: Dict[str, DendriteElement]

    def __init__(self, data: Dict[str, DendriteElement]):
        self._data = data

    def __getattr__(self, name: str) -> DendriteElement:
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    def __getitem__(self, key: str) -> DendriteElement:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._data})"


class DendritePage:
    _file_chooser: Optional[FileChooser]
    _download: Optional[Download]

    def __init__(self, page: Page, dendrite_browser: DendriteBrowser):
        self.page = page
        self.screenshot_manager = ScreenshotManager()
        self.dendrite_browser = dendrite_browser
        self._file_chooser_set_event = asyncio.Event()
        self._download_set_event = asyncio.Event()
        self.selector_manager = SelectorManager(self, dendrite_browser)
        self.browser_api_client = dendrite_browser.browser_api_client

    @property
    def url(self):
        return self.page.url

    @property
    def keyboard(self) -> Keyboard:
        return self.page.keyboard

    def get_playwright_page(self) -> Page:
        return self.page

    async def goto(
        self,
        url: str,
        timeout: Optional[float] = 30000,
        wait_until: Optional[
            Literal["commit", "domcontentloaded", "load", "networkidle"]
        ] = "load",
    ) -> None:
        await self.page.goto(url, timeout=timeout, wait_until=wait_until)

    async def upload_files(
        self,
        files: Union[
            str,
            pathlib.Path,
            FilePayload,
            Sequence[Union[str, pathlib.Path]],
            Sequence[FilePayload],
        ],
        timeout: float = 30,
    ) -> None:
        file_chooser = await self._get_file_chooser(timeout)
        await file_chooser.set_files(files)

    async def _get_file_chooser(self, timeout: float = 30) -> FileChooser:
        try:
            await asyncio.wait_for(self._file_chooser_set_event.wait(), timeout)
            if not self._file_chooser:
                raise Exception("The file chooser was not set.")
            fc = self._file_chooser

            self._file_chooser = None
            self._file_chooser_set_event.clear()
            return fc
        except asyncio.TimeoutError:
            raise TimeoutError(
                "The File Chooser was not set within the specified timeout."
            )

    def _set_file_chooser(self, file_chooser: FileChooser):
        self._file_chooser = file_chooser
        self._file_chooser_set_event.set()

    async def get_download(self, timeout: float = 30):
        try:
            await asyncio.wait_for(self._download_set_event.wait(), timeout)
            if not self._download:
                raise Exception("No download was not found.")
            download = self._download

            self._download = None
            self._download_set_event.clear()
            return download
        except asyncio.TimeoutError:
            raise TimeoutError(
                "There was no download event set within the specified timeout."
            )

    def _set_download(self, download: Download):
        self._download = download
        self._download_set_event.set()

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[str],
        use_cache: bool = True,
    ) -> ScrapePageResponse[str]: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[bool],
        use_cache: bool = True,
    ) -> ScrapePageResponse[bool]: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[int],
        use_cache: bool = True,
    ) -> ScrapePageResponse[int]: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[float],
        use_cache: bool = True,
    ) -> ScrapePageResponse[float]: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[PydanticModel],
        use_cache: bool = True,
    ) -> ScrapePageResponse[PydanticModel]: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: JsonSchema,
        use_cache: bool = True,
    ) -> ScrapePageResponse[JsonSchema]: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: None = None,
        use_cache: bool = True,
    ) -> ScrapePageResponse[Any]: ...

    async def extract(
        self,
        prompt: str,
        type_spec: Optional[TypeSpec] = None,
        use_cache: bool = True,
    ) -> ScrapePageResponse:
        json_schema = None
        if type_spec:
            json_schema = to_json_schema(type_spec)

        try_run_dto = TryRunScriptDTO(
            url=self.page.url,
            raw_html=str(await self.get_soup()),
            llm_config=self.dendrite_browser.get_llm_config(),
            prompt=prompt,
            return_data_json_schema=json_schema,
        )

        res = await self.browser_api_client.try_run_cached(try_run_dto)
        if res == None:
            page_information = await self.get_page_information()
            scrape_dto = ScrapePageDTO(
                page_information=page_information,
                llm_config=self.dendrite_browser.get_llm_config(),
                prompt=prompt,
                return_data_json_schema=json_schema,
                use_screenshot=True,
                use_cache=use_cache,
            )
            res = await self.browser_api_client.scrape_page(scrape_dto)

        converted_res = res.return_data
        if type_spec != None:
            converted_res = convert_to_type_spec(type_spec, res.return_data)

        res.return_data = converted_res

        return res

    async def scroll_to_bottom(self):
        # TODO: add timeout
        i = 0
        last_scroll_position = 0
        start_time = time.time()

        while True:
            current_scroll_position = await self.page.evaluate("window.scrollY")

            await self.page.evaluate(f"window.scrollTo(0, {i})")
            i += 1000

            if time.time() - start_time > 2.0:
                break

            if current_scroll_position - last_scroll_position > 1000:
                start_time = time.time()

            last_scroll_position = current_scroll_position

            await asyncio.sleep(0.1)

    async def get_element_from_dendrite_id(
        self, soup: BeautifulSoup, dendrite_id: str
    ) -> Locator:
        try:
            element = soup.find(attrs={"d-id": dendrite_id})
            frame = self._get_context(element)

            el = frame.locator(f"xpath=//*[@d-id='{dendrite_id}']")
            await el.wait_for(timeout=3000)
            return el.first
        except Exception as e:
            logger.debug(
                f"Could not find element with the dendrite id {dendrite_id}: {e}"
            )
            raise Exception(
                f"Could not find element with the dendrite id {dendrite_id}"
            )

    def _get_context(self, element: Any) -> Union[Page, FrameLocator]:
        context = self.page

        if isinstance(element, Tag):
            full_path = element.get("iframe-path")
            if full_path:
                for path in full_path.split("|"):  # type: ignore
                    context = context.frame_locator(f"xpath=//iframe[@d-id='{path}']")

        return context

    async def get_page_information(self) -> PageInformation:
        start_time = time.time()
        soup = await self.get_soup()

        base64 = await self.screenshot_manager.take_full_page_screenshot(self.page)
        print("time to get all: ", time.time() - start_time)

        return PageInformation(
            url=self.page.url,
            raw_html=str(soup),
            screenshot_base64=base64,
        )

    async def generate_dendrite_ids(self):
        tries = 0
        while tries < 3:
            try:
                await self.page.evaluate(GENERATE_DENDRITE_IDS_SCRIPT)
                return
            except Exception as e:
                await self.page.wait_for_load_state(state="load", timeout=3000)
                print(f"Failed to generate dendrite IDs: {e}, retrying")
                tries += 1

        raise Exception("Failed to add d-ids to DOM.")

    async def scroll_through_entire_page(self) -> None:
        await self.scroll_to_bottom()

    async def wait_for(
        self,
        prompt: str,
        timeout: float = 2,
        max_retries: int = 5,
    ):
        llm_config = self.dendrite_browser.get_llm_config()

        num_attempts = 0
        while num_attempts < max_retries:
            num_attempts += 1
            await asyncio.sleep(timeout)
            try:

                page_information = await self.get_page_information()
                prompt = f"Prompt: '{prompt}'\n\nReturn a boolean that determines if the requested information or thing is available on the page."
                res = await self.ask(prompt, bool)
                if res.return_data:
                    return res
            except Exception as e:
                logger.debug(f"Waited for page, but got this exception: {e}")
                continue

        page_information = await self.get_page_information()
        raise DendriteException(
            message=f"Retried {max_retries} times but failed to wait for the requested condition.",
            screenshot_base64=page_information.screenshot_base64,
        )

    @overload
    async def ask(self, prompt: str, type_spec: Type[str]) -> AskPageResponse[str]: ...

    @overload
    async def ask(
        self, prompt: str, type_spec: Type[bool]
    ) -> AskPageResponse[bool]: ...

    @overload
    async def ask(self, prompt: str, type_spec: Type[int]) -> AskPageResponse[int]: ...

    @overload
    async def ask(
        self, prompt: str, type_spec: Type[float]
    ) -> AskPageResponse[float]: ...

    @overload
    async def ask(
        self, prompt: str, type_spec: Type[PydanticModel]
    ) -> AskPageResponse[PydanticModel]: ...

    @overload
    async def ask(
        self, prompt: str, type_spec: JsonSchema
    ) -> AskPageResponse[JsonSchema]: ...

    @overload
    async def ask(
        self, prompt: str, type_spec: None = None
    ) -> AskPageResponse[JsonSchema]: ...

    async def ask(
        self,
        prompt: str,
        type_spec: Optional[TypeSpec] = None,
    ) -> AskPageResponse[Any]:
        llm_config = self.dendrite_browser.get_llm_config()
        page_information = await self.get_page_information()

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
            if type_spec != None:
                converted_res = convert_to_type_spec(type_spec, res.return_data)

            return AskPageResponse(
                return_data=converted_res, description=res.description
            )
        except Exception as e:
            raise DendriteException(
                message=f"Failed to ask page: {e}",
                screenshot_base64=page_information.screenshot_base64,
            )

    @overload
    async def get_elements(
        self,
        prompt_or_elements: str,
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 3,
        context: str = "",
    ) -> List[DendriteElement]: ...

    @overload
    async def get_elements(
        self,
        prompt_or_elements: Dict[str, str],
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 3,
        context: str = "",
    ) -> DendriteElementsResponse: ...

    async def get_elements(
        self,
        prompt_or_elements: Union[str, Dict[str, str]],
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 3,
        context: str = "",
    ) -> Union[List[DendriteElement], DendriteElementsResponse]:
        llm_config = self.dendrite_browser.get_llm_config()

        if isinstance(prompt_or_elements, str):
            num_attempts = 0
            while num_attempts < max_retries:
                num_attempts += 1
                page_information = await self.get_page_information()
                dto = GetElementsDTO(
                    page_information=page_information,
                    llm_config=llm_config,
                    prompt=prompt_or_elements,
                    use_cache=use_cache,
                    only_one=False,
                )
                selectors = await self.browser_api_client.get_interactions_selector(dto)
                if not selectors:
                    raise DendriteException(
                        message="Could not find suitable elements on the page.",
                        screenshot_base64=page_information.screenshot_base64,
                    )

                for selector in reversed(selectors["selectors"]):
                    try:
                        dendrite_elements = (
                            await self.selector_manager.get_all_elements_from_selector(
                                selector
                            )
                        )
                        return dendrite_elements
                    except Exception as e:
                        print("Error getting all selectors: ", e)

                await asyncio.sleep(timeout)

            page_information = await self.get_page_information()
            raise DendriteException(
                message="Could not find suitable elements on the page.",
                screenshot_base64=page_information.screenshot_base64,
            )

        elif isinstance(prompt_or_elements, dict):

            tasks = []
            for field_name, prompt in prompt_or_elements.items():
                full_prompt = f"{prompt}\n\nHere is some extra context: {context}"
                task = self.get_element(
                    full_prompt,
                    use_cache=use_cache,
                    max_retries=max_retries,
                    timeout=timeout,
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            elements_dict: Dict[str, DendriteElement] = {}
            for element, field_name in zip(results, prompt_or_elements.keys()):
                elements_dict[field_name] = element

            return DendriteElementsResponse(elements_dict)

        else:
            raise ValueError("Input must be either a string prompt or a dictionary")

    async def get_element(
        self,
        prompt: str,
        use_cache=True,
        max_retries=3,
        timeout=3,
    ) -> DendriteElement:
        llm_config = self.dendrite_browser.get_llm_config()

        num_attempts = 0
        while num_attempts < max_retries:
            num_attempts += 1

            page_information = await self.get_page_information()
            dto = GetElementsDTO(
                page_information=page_information,
                llm_config=llm_config,
                prompt=prompt,
                only_one=True,
                use_cache=use_cache,
            )

            suitable_selectors = (
                await self.browser_api_client.get_interactions_selector(dto)
            )
            print("suitable_selectors from server: ", suitable_selectors)

            if not suitable_selectors:
                raise DendriteException(
                    message="Could not find suitable element on the page.",
                    screenshot_base64=page_information.screenshot_base64,
                )

            for selector in reversed(suitable_selectors["selectors"]):
                try:
                    print("selector we are trying: ", selector)
                    dendrite_elements = (
                        await self.selector_manager.get_all_elements_from_selector(
                            selector
                        )
                    )
                    print("returned these elements: ", dendrite_elements)

                    return dendrite_elements[0]
                except Exception as e:
                    print("Error getting all selectors: ", e)

            await asyncio.sleep(timeout)

        page_information = await self.get_page_information()
        raise DendriteException(
            message="Could not find suitable element on the page.",
            screenshot_base64=page_information.screenshot_base64,
        )

    async def get_content(self):
        return await self.page.content()

    async def get_soup(self, ) -> BeautifulSoup:
        await self.generate_dendrite_ids()

        page_source = await self.page.content()
        soup = BeautifulSoup(page_source, "lxml")
        await self._expand_iframes(soup)


        return soup

    async def _expand_iframes(self, page_source: BeautifulSoup):
        await expand_iframes(self.page, page_source)

    async def get_invisible_d_ids(self) -> set[str]:
        script = """() => {
            var elements = document.querySelectorAll('[d-id]');
            var invisibleDendriteIds = [];
            for (var i = 0; i < elements.length; i++) {
                const element = elements[i]
                const style = window.getComputedStyle(element);
                const isVisible = style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
                const tagName = element.tagName.toLowerCase();
                if (tagName != 'html' && tagName != 'body') {
                    if(!isVisible){
                        invisibleDendriteIds.push(element.getAttribute('d-id'));
                    }
                }
            }
            return invisibleDendriteIds;
        }
        """
        res = await self.get_playwright_page().evaluate(script)
        return set(res)

    async def _dump_html(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(await self.page.content())

    async def upload_file(self):
        self.page.expect_file_chooser()
