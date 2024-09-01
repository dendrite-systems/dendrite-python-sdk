from pydantic import BaseModel

from dendrite_sdk._core.models.llm_config import LLMConfig
from dendrite_sdk._core.models.page_information import PageInformation


class GetElementsDTO(BaseModel):
    page_information: PageInformation
    llm_config: LLMConfig
    prompt: str
    use_cache: bool = True
    only_one: bool
