from typing import (
    TYPE_CHECKING,
    List,
    Optional,
)
from loguru import logger

from pydantic import BaseModel
from dendrite_python_sdk.dendrite_browser.DendriteElement import DendriteElement
from dendrite_python_sdk.responses.ScrapePageResponse import ScrapePageResponse

from typing import TYPE_CHECKING, List


if TYPE_CHECKING:
    from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage
    from dendrite_python_sdk.dendrite_browser.DendriteBrowser import DendriteBrowser


class TestSelectorResult(BaseModel):
    exception_when_selecting: Optional[str] = None
    amount_selected: Optional[int] = 0


class SelectorManager:
    def __init__(
        self, dendrite_page: "DendritePage", dendrite_browser: "DendriteBrowser"
    ):
        self.dendrite_page = dendrite_page
        self.dendrite_browser = dendrite_browser

    async def get_all_elements_from_selector(
        self, selector: str
    ) -> List[DendriteElement]:
        dendrite_elements: List[DendriteElement] = []
        soup = await self.dendrite_page.get_soup()
        elements = soup.select(selector)

        for element in elements:
            frame = self.dendrite_page._get_context(element)
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
