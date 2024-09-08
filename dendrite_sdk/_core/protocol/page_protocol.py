from asyncio import Protocol
from typing import Any, List

from dendrite_sdk._api.browser_api_client import BrowserAPIClient
from dendrite_sdk._core._base_browser import BaseDendriteBrowser
from dendrite_sdk._core.dendrite_element import DendriteElement


class DendritePageProtocol(Protocol):
    """
    Protocol that specifies the required methods and attributes
    for the `ExtractionMixin` to work.
    """

    dendrite_browser: BaseDendriteBrowser
    browser_api_client: BrowserAPIClient

    async def _get_page_information(self) -> Any: ...

    async def get_all_elements_from_selector(
        self, selector: str
    ) -> List[DendriteElement]: ...