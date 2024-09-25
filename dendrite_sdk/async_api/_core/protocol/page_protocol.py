from typing import Any, List, TYPE_CHECKING, Protocol

from dendrite_sdk.async_api._api.browser_api_client import BrowserAPIClient
from dendrite_sdk.async_api._core.models.page_information import PageInformation

if TYPE_CHECKING:
    from dendrite_sdk.async_api._core._base_browser import BaseAsyncDendrite
from dendrite_sdk.async_api._core.dendrite_element import AsyncElement


class DendritePageProtocol(Protocol):
    """
    Protocol that specifies the required methods and attributes
    for the `ExtractionMixin` to work.
    """

    dendrite_browser: "BaseAsyncDendrite"
    browser_api_client: BrowserAPIClient

    async def _get_page_information(self) -> PageInformation: ...

    async def _get_all_elements_from_selector(
        self, selector: str
    ) -> List[AsyncElement]: ...
