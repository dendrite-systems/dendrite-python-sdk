from pydantic import BaseModel

from dendrite_python_sdk.models.PageInformation import PageInformation
from dendrite_python_sdk.models.LLMConfig import LLMConfig


class GetInteractionDTO(BaseModel):
    page_information: PageInformation
    llm_config: LLMConfig
    prompt: str
