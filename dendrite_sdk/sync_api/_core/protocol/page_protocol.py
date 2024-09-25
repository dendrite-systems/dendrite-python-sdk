from typing import Any, List, TYPE_CHECKING, Protocol
from dendrite_sdk.sync_api._api.browser_api_client import BrowserAPIClient
from dendrite_sdk.sync_api._core.models.page_information import PageInformation

if TYPE_CHECKING:
    from dendrite_sdk.sync_api._core._base_browser import BaseDendriteBrowser
from dendrite_sdk.sync_api._core.dendrite_element import DendriteElement


class DendritePageProtocol(Protocol):
    """
    Protocol that specifies the required methods and attributes
    for the `ExtractionMixin` to work.
    """

    dendrite_browser: "BaseDendriteBrowser"
    browser_api_client: BrowserAPIClient

    def _get_page_information(self) -> PageInformation: ...

    def _get_all_elements_from_selector(
        self, selector: str
    ) -> List[DendriteElement]: ...
