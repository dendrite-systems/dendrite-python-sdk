from typing import TYPE_CHECKING, Protocol

from dendrite_sdk.async_api._api.browser_api_client import BrowserAPIClient

if TYPE_CHECKING:
    from dendrite_sdk.async_api._core.dendrite_page import AsyncPage
    from dendrite_sdk.async_api._core.dendrite_browser import AsyncDendrite


class DendritePageProtocol(Protocol):
    """
    Protocol that specifies the required methods and attributes
    for the `ExtractionMixin` to work.
    """

    def _get_dendrite_browser(self) -> "AsyncDendrite": ...

    def _get_browser_api_client(self) -> BrowserAPIClient: ...

    async def _get_page(self) -> "AsyncPage": ...
