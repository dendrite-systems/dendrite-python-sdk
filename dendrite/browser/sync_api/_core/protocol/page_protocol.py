from typing import TYPE_CHECKING, Protocol
from dendrite.logic.interfaces import SyncProtocol

if TYPE_CHECKING:
    from dendrite.browser.sync_api._core.dendrite_browser import Dendrite
    from dendrite.browser.sync_api._core.dendrite_page import Page


class DendritePageProtocol(Protocol):
    """
    Protocol that specifies the required methods and attributes
    for the `ExtractionMixin` to work.
    """

    def _get_dendrite_browser(self) -> "Dendrite": ...

    def _get_logic_api(self) -> SyncProtocol: ...

    def _get_page(self) -> "Page": ...
