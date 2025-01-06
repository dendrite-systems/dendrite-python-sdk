from typing import TYPE_CHECKING, Protocol
from dendrite.logic import LogicEngine

if TYPE_CHECKING:
    from ..dendrite_browser import Dendrite
    from ..dendrite_page import Page


class DendritePageProtocol(Protocol):
    """
    Protocol that specifies the required methods and attributes
    for the `ExtractionMixin` to work.
    """

    @property
    def logic_engine(self) -> LogicEngine: ...

    @property
    def dendrite_browser(self) -> "Dendrite": ...

    def _get_page(self) -> "Page": ...
