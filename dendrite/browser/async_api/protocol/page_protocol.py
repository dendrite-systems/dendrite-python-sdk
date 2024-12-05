from typing import TYPE_CHECKING, Protocol

from dendrite.logic import AsyncLogicEngine

if TYPE_CHECKING:
    from ..dendrite_browser import AsyncDendrite
    from ..dendrite_page import AsyncPage


class DendritePageProtocol(Protocol):
    """
    Protocol that specifies the required methods and attributes
    for the `ExtractionMixin` to work.
    """

    @property
    def logic_engine(self) -> AsyncLogicEngine: ...

    @property
    def dendrite_browser(self) -> "AsyncDendrite": ...

    async def _get_page(self) -> "AsyncPage": ...
