from typing import Any
from pydantic import BaseModel
from dendrite_python_sdk.models.LLMConfig import LLMConfig

from dendrite_python_sdk.models.PageInformation import PageInformation


class GetElementsDTO(BaseModel):
    page_information: PageInformation
    llm_config: LLMConfig
    prompt: str
    use_cache: bool = True
    only_one: bool
