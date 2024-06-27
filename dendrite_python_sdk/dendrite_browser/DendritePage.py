from __future__ import annotations
import asyncio
import json
import time

from playwright.async_api import Page, Locator
from bs4 import BeautifulSoup, Tag

from typing import TYPE_CHECKING, Any, List, Optional, Type
from pydantic import BaseModel

from dendrite_python_sdk.dto.ScrapePageDTO import ScrapePageDTO
from dendrite_python_sdk.exceptions.DendriteException import DendriteException
from dendrite_python_sdk.responses.ScrapePageResponse import ScrapePageResponse

if TYPE_CHECKING:
    from dendrite_python_sdk import DendriteBrowser

from dendrite_python_sdk.dendrite_browser.ScreenshotManager import ScreenshotManager
from dendrite_python_sdk.dendrite_browser.utils import (
    get_interactive_elements_with_playwright,
)
from dendrite_python_sdk.dto.GetInteractionDTO import GetInteractionDTO
from dendrite_python_sdk.models.PageInformation import PageInformation
from dendrite_python_sdk.dendrite_browser.DendriteLocator import DendriteLocator
from dendrite_python_sdk.request_handler import (
    get_interaction,
    get_interactions,
    get_interactions_selector,
    scrape_page,
)


class DendritePage:
    def __init__(self, page: Page, dendrite_browser: DendriteBrowser):
        self.page = page
        self.screenshot_manager = ScreenshotManager()
        self.dendrite_browser = dendrite_browser

    @property
    def url(self):
        return self.page.url

    def get_playwright_page(self) -> Page:
        return self.page

    async def scrape(
        self,
        prompt: str,
        expected_return_data: Optional[str] = None,
        return_data_json_schema: Optional[Any] = None,
        pydantic_return_model: Optional[Type[BaseModel]] = None,
    ) -> Any:

        json_schema = return_data_json_schema
        if pydantic_return_model:
            json_schema = json.loads(pydantic_return_model.schema_json())

        page_information = await self.get_page_information()
        dto = ScrapePageDTO(
            page_information=page_information,
            llm_config=self.dendrite_browser.get_llm_config(),
            prompt=prompt,
            expected_return_data=expected_return_data,
            return_data_json_schema=json_schema,
        )
        res = await scrape_page(dto)

        if pydantic_return_model:
            return pydantic_return_model.parse_obj(res.json_data)

        return res.json_data

    async def scroll_to_bottom(self):
        # TODO: add timeout
        i = 0
        last_scroll_position = 0
        start_time = time.time()

        while True:
            current_scroll_position = await self.page.evaluate("window.scrollY")

            await self.page.evaluate(f"window.scrollTo(0, {i})")
            i += 20000

            if time.time() - start_time > 2.0:
                break

            if current_scroll_position - last_scroll_position > 1000:
                start_time = time.time()

            last_scroll_position = current_scroll_position

            await asyncio.sleep(0.5)

    async def get_element_from_dendrite_id(self, dendrite_id: str) -> Locator:
        try:
            await self.generate_dendrite_ids()
            el = self.page.locator(f"xpath=//*[@d-id='{dendrite_id}']")
            await el.wait_for(timeout=3000)
            return el.first
        except Exception as e:
            raise Exception(
                f"Could not find element with the dendrite id {dendrite_id}"
            )

    async def get_elements_from_dendrite_ids(
        self, dendrite_ids: List[str]
    ) -> List[Locator]:
        try:
            await self.generate_dendrite_ids()

            element_list = []
            for id in dendrite_ids:
                el = await self.get_element_from_dendrite_id(id)
                element_list.append(el)

            return element_list
        except Exception as e:
            raise Exception(
                f"Could not find elements with the dendrite ids {dendrite_ids}, exception: {e}"
            )

    async def get_page_information(
        self, only_visible_elements_in_html: bool = False
    ) -> PageInformation:
        start_time = time.time()
        soup_task = self.get_soup(only_visible_elements=only_visible_elements_in_html)
        # print("soup: ", soup)
        interactable_elements_task = get_interactive_elements_with_playwright(self.page)
        # print("interactable_elements: ", interactable_elements)
        base64_task = self.screenshot_manager.take_full_page_screenshot(self.page)
        soup, interactable_elements, base64 = await asyncio.gather(
            soup_task, interactable_elements_task, base64_task
        )
        print("time to get all: ", time.time() - start_time)

        return PageInformation(
            url=self.page.url,
            raw_html=str(soup),
            interactable_element_info=interactable_elements,
            screenshot_base64=base64,
        )

    async def generate_dendrite_ids(self):
        tries = 0
        while tries < 3:
            # print("tries: ", tries)
            script = """
var hashCode = (string) => {
    var hash = 0, i, chr;
    if (string.length === 0) return hash;
    for (i = 0; i < string.length; i++) {
        chr = string.charCodeAt(i);
        hash = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
}

var getXPathForElement = (element) => {
    const idx = (sib, name) => sib
        ? idx(sib.previousElementSibling, name||sib.localName) + (sib.localName == name)
        : 1;
    const segs = elm => !elm || elm.nodeType !== 1
        ? ['']
        : elm.id && document.getElementById(elm.id) === elm
            ? [`id("${elm.id}")`]
            : [...segs(elm.parentNode), `${elm.localName.toLowerCase()}[${idx(elm)}]`];
    return segs(element).join('/');
}

document.querySelectorAll('*').forEach((element, index) => {
    const xpath = getXPathForElement(element)
    const uniqueId = hashCode(xpath).toString(36);
    element.setAttribute('d-id', uniqueId);
});

"""
            try:
                await self.page.evaluate(script)
                return
            except Exception as e:
                await self.page.wait_for_load_state(state="load", timeout=3000)
                print(f"Failed to generate dendrite IDs: {e}, retrying")
                tries += 1

        raise Exception("Failed to add d-ids to DOM.")

    async def scroll_through_entire_page(self) -> None:
        await self.scroll_to_bottom()

    async def get_interactions_selector(
        self,
        prompt: str,
        db_prompt: Optional[str] = None,
        force_use_cache: bool = False,
    ) -> List[DendriteLocator]:
        llm_config = self.dendrite_browser.get_llm_config()

        page_information = await self.get_page_information(
            only_visible_elements_in_html=True
        )

        dto = ScrapePageDTO(
            page_information=page_information,
            llm_config=llm_config,
            prompt=prompt,
            db_prompt=db_prompt,
            return_data_json_schema=None,
            expected_return_data=None,
            force_use_cache=force_use_cache,
        )

        res = await get_interactions_selector(dto)
        if res:
            # print("selectors: ", res["selectors"])
            selectors = res["selectors"]
            for selector in selectors:
                try:
                    locators = []
                    locator = self.page.locator(selector)
                    # print("locator: ", locator)
                    count = await locator.count()
                    # print("count: ", count)

                    for index in range(count):
                        try:
                            nth_locator = locator.nth(index)
                            d_id = await nth_locator.get_attribute("d-id", timeout=0)
                            if d_id:
                                dendrite_locater = DendriteLocator(
                                    locator=nth_locator,
                                    dendrite_id=d_id,
                                    dendrite_browser=self.dendrite_browser,
                                )
                                locators.append(dendrite_locater)
                        except Exception as e:
                            print("Error getting this selector: ", e)

                    print("selector locators: ", locators)
                    if len(locators) == 0:
                        continue

                    return locators
                except Exception as e:
                    print("Error getting all selectors: ", e)

        return []
        # page_information = await self.get_page_information()
        # raise DendriteException(
        #     message="Could not find suitable element on the page.",
        #     screenshot_base64=page_information.screenshot_base64,
        # )

    async def get_interactable_elements(
        self,
        prompt: str,
        timeout: float = 0.5,
        max_retries: int = 3,
    ) -> List[DendriteLocator]:
        llm_config = self.dendrite_browser.get_llm_config()

        num_attempts = 0
        while num_attempts < max_retries:
            page_information = await self.get_page_information(
                only_visible_elements_in_html=True
            )

            dto = GetInteractionDTO(
                page_information=page_information, llm_config=llm_config, prompt=prompt
            )

            res = await get_interactions(dto)
            if res:
                locators = await self.get_elements_from_dendrite_ids(
                    res["dendrite_ids"]
                )
                dendrite_locators = [
                    DendriteLocator(id, locator, self.dendrite_browser)
                    for id, locator in zip(res["dendrite_ids"], locators)
                ]
                return dendrite_locators
            num_attempts += 1
            await asyncio.sleep(timeout)

        page_information = await self.get_page_information()
        raise DendriteException(
            message="Could not find suitable element on the page.",
            screenshot_base64=page_information.screenshot_base64,
        )

    async def get_interactable_element(
        self,
        prompt: str,
        timeout: float = 0.5,
        max_retries: int = 3,
    ) -> DendriteLocator:
        llm_config = self.dendrite_browser.get_llm_config()

        num_attempts = 0
        while num_attempts < max_retries:
            page_information = await self.get_page_information(
                only_visible_elements_in_html=True
            )

            dto = GetInteractionDTO(
                page_information=page_information, llm_config=llm_config, prompt=prompt
            )

            res = await get_interaction(dto)
            if res and res["dendrite_id"] != "":
                try:
                    locator = await self.get_element_from_dendrite_id(
                        res["dendrite_id"]
                    )
                except:
                    continue
                dendrite_locator = DendriteLocator(
                    res["dendrite_id"], locator, self.dendrite_browser
                )
                return dendrite_locator
            num_attempts += 1
            await asyncio.sleep(timeout)

        page_information = await self.get_page_information()
        raise DendriteException(
            message="Could not find suitable element on the page.",
            screenshot_base64=page_information.screenshot_base64,
        )

    async def get_content(self):
        return await self.page.content()

    async def get_soup(self, only_visible_elements: bool = False) -> BeautifulSoup:
        start_time = time.time()
        await self.generate_dendrite_ids()
        print("time to generate Ids: ", time.time() - start_time)

        page_source = await self.page.content()
        soup = BeautifulSoup(page_source, "lxml")
        if only_visible_elements:
            start_time = time.time()
            invisible_d_ids = await self.get_invisible_d_ids()
            print("time to get invis ids: ", time.time() - start_time)
            elems = soup.find_all(attrs={"d-id": True})

            for elem in elems:
                if elem.attrs["d-id"] in invisible_d_ids:
                    elem.extract()

        return soup

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
