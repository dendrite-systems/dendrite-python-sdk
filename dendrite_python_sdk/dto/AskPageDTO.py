from typing import Any, Optional
from pydantic import BaseModel
from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.models.PageInformation import PageInformation


class AskPageDTO(BaseModel):
    prompt: str
    return_schema: Optional[Any]
    page_information: PageInformation
    llm_config: LLMConfig
