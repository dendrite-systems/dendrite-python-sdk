from typing import Any, Optional
from pydantic import BaseModel
from dendrite_sdk._core.models.llm_config import LLMConfig
from dendrite_sdk._core.models.page_information import PageInformation


class AskPageDTO(BaseModel):
    prompt: str
    return_schema: Optional[Any]
    page_information: PageInformation
    llm_config: LLMConfig
