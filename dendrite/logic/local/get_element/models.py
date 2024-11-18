from dataclasses import dataclass
from typing import NamedTuple, Optional

from dendrite.browser._common.types import Status


class ExpandedTag(NamedTuple):
    d_id: str
    html: str


@dataclass
class Interactable:
    status: Status
    reason: str
    dendrite_id: Optional[str] = None
