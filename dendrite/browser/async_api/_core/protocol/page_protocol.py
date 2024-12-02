from typing import TYPE_CHECKING, Protocol

from dendrite.logic.hosted._api.browser_api_client import BrowserAPIClient
from dendrite.logic.interfaces import AsyncProtocol

if TYPE_CHECKING:
    from dendrite.browser.async_api._core.dendrite_browser import AsyncDendrite
    from dendrite.browser.async_api._core.dendrite_page import AsyncPage


class DendritePageProtocol(Protocol):
    """
    Protocol that specifies the required methods and attributes
    for the `ExtractionMixin` to work.
    """

    def _get_dendrite_browser(self) -> "AsyncDendrite": ...

    def _get_logic_api(self) -> AsyncProtocol: ...

    async def _get_page(self) -> "AsyncPage": ...
