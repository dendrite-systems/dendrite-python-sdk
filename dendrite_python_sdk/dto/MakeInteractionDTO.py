from typing import Literal, Optional
from pydantic import BaseModel
from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.models.PageDeltaInformation import PageDeltaInformation


InteractionType = Literal["click", "fill"]


class MakeInteractionDTO(BaseModel):
    url: str
    dendrite_id: str
    interaction_type: InteractionType
    value: Optional[str] = None
    expected_outcome: Optional[str]
    page_delta_information: PageDeltaInformation
    llm_config: LLMConfig
