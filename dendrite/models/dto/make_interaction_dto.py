from typing import Literal, Optional

from pydantic import BaseModel

from dendrite.models.page_information import PageDiffInformation

InteractionType = Literal["click", "fill", "hover"]


class VerifyActionDTO(BaseModel):
    url: str
    dendrite_id: str
    interaction_type: InteractionType
    tag_name: str
    value: Optional[str] = None
    expected_outcome: str
    screenshot_before: str
    screenshot_after: str
