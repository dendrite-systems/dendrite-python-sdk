from typing import Optional
from pydantic import BaseModel
from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.models.PageInformation import PageInformation


class GoogleSearchDTO(BaseModel):
    query: str
    country: Optional[str] = None
    filter_results_prompt: Optional[str] = None
    page_information: PageInformation
    llm_config: LLMConfig
