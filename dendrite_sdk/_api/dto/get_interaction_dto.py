from pydantic import BaseModel

from dendrite_sdk._core.models.llm_config import LLMConfig
from dendrite_sdk._core.models.page_information import PageInformation


class GetInteractionDTO(BaseModel):
    page_information: PageInformation
    llm_config: LLMConfig
    prompt: str
