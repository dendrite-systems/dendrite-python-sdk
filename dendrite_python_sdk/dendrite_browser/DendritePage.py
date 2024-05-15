from __future__ import annotations

from playwright.async_api import Page, Locator
from bs4 import BeautifulSoup

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dendrite_python_sdk import DendriteBrowser

from dendrite_python_sdk.dendrite_browser.ScreenshotManager import ScreenshotManager
from dendrite_python_sdk.dendrite_browser.utils import (
    get_interactive_elements_with_playwright,
)
from dendrite_python_sdk.dto.GetInteractionDTO import GetInteractionDTO
from dendrite_python_sdk.models.PageInformation import PageInformation
from dendrite_python_sdk.request_handler import get_interaction
from dendrite_python_sdk.dendrite_browser.DendriteLocator import DendriteLocator


class DendritePage:
    def __init__(self, page: Page, dendrite_browser: DendriteBrowser):
        self.page = page
        self.screenshot_manager = ScreenshotManager()
        self.dendrite_browser = dendrite_browser

    @property
    def url(self):
        return self.page.url

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

    async def get_interactable_element(self, prompt: str) -> DendriteLocator:
        page_information = await self.get_page_information()

        llm_config = self.dendrite_browser.get_llm_config()
        dto = GetInteractionDTO(
            page_information=page_information, llm_config=llm_config, prompt=prompt
        )
        res = await get_interaction(dto)
        print("res: ", res)
        if res:
            locator = await self.get_element_from_dendrite_id(res["dendrite_id"])
            dendrite_locator = DendriteLocator(
                res["dendrite_id"], locator, self.dendrite_browser
            )
            return dendrite_locator

        raise Exception("Could not find suitable element on the page.")

    async def get_soup(self) -> BeautifulSoup:
        await self.generate_dendrite_ids()
        page_source = await self.page.content()
        soup = BeautifulSoup(page_source, "lxml")
        return soup
