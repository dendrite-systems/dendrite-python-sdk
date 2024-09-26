from typing import TYPE_CHECKING, Protocol
from dendrite_sdk.sync_api._api.browser_api_client import BrowserAPIClient

if TYPE_CHECKING:
    from dendrite_sdk.sync_api._core.dendrite_page import Page
    from dendrite_sdk.sync_api._core._base_browser import BaseDendrite


class DendritePageProtocol(Protocol):
    """
    Protocol that specifies the required methods and attributes
    for the `ExtractionMixin` to work.
    """

    def _get_dendrite_browser(self) -> "BaseDendrite": ...

    def _get_browser_api_client(self) -> BrowserAPIClient: ...

    def _get_page(self) -> "Page": ...
