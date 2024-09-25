from typing import Literal, Optional
from pydantic import BaseModel
from dendrite_sdk._core.models.api_config import APIConfig
from dendrite_sdk._core.models.page_diff_information import PageDiffInformation


InteractionType = Literal["click", "fill", "hover"]


class MakeInteractionDTO(BaseModel):
    url: str
    dendrite_id: str
    interaction_type: InteractionType
    value: Optional[str] = None
    expected_outcome: Optional[str]
    page_delta_information: PageDiffInformation
    api_config: APIConfig
