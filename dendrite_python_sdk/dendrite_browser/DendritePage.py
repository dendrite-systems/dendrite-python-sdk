from __future__ import annotations
import asyncio
import json
import time

from playwright.async_api import Page, Locator
from bs4 import BeautifulSoup

from typing import TYPE_CHECKING, Any, Optional, Type
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
from dendrite_python_sdk.request_handler import get_interaction, scrape_page


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
        i = 0
        last_scroll_position = 0
        start_time = time.time()

        while True:
            current_scroll_position = await self.page.evaluate("window.scrollY")

            await self.page.evaluate(f"window.scrollTo(0, {i})")
            i += 20000

            if time.time() - start_time > 2:
                break

            if current_scroll_position - last_scroll_position > 1000:
                start_time = time.time()

            last_scroll_position = current_scroll_position

            await asyncio.sleep(0.5)

    async def get_element_from_dendrite_id(self, dendrite_id: str) -> Locator:
        try:
            await self.generate_dendrite_ids()
            el = self.page.locator(f"xpath=//*[@d-id='{dendrite_id}']")
            await el.wait_for(timeout=500)
            return el.first
        except Exception as e:
            raise Exception(
                f"Could not find element with the dendrite id {dendrite_id}"
            )

    async def get_page_information(self) -> PageInformation:
        soup = await self.get_soup()
        interactable_elements = await get_interactive_elements_with_playwright(
            self.page
        )
        base64 = await self.screenshot_manager.take_viewport_screenshot(self.page)

        return PageInformation(
            url=self.page.url,
            raw_html=str(soup),
            interactable_element_info=interactable_elements,
            screenshot_base64=base64,
        )

    async def generate_dendrite_ids(self):
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

        await self.page.evaluate(script)

    async def scroll_through_entire_page(self) -> None:
        await self.scroll_to_bottom()

    async def get_interactable_element(
        self,
        prompt: str,
        timeout: float = 0.5,
        max_retries: int = 3,
    ) -> DendriteLocator:
        llm_config = self.dendrite_browser.get_llm_config()

        num_attempts = 0
        while num_attempts < max_retries:
            page_information = await self.get_page_information()

            dto = GetInteractionDTO(
                page_information=page_information, llm_config=llm_config, prompt=prompt
            )

            res = await get_interaction(dto)
            print("res: ", res)
            if res and res["dendrite_id"] != "":
                locator = await self.get_element_from_dendrite_id(res["dendrite_id"])
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

    async def get_soup(self) -> BeautifulSoup:
        await self.generate_dendrite_ids()
        page_source = await self.page.content()
        soup = BeautifulSoup(page_source, "lxml")
        return soup
