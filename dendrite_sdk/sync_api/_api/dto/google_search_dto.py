from typing import Optional
from pydantic import BaseModel
from dendrite_sdk.sync_api._core.models.llm_config import LLMConfig
from dendrite_sdk.sync_api._core.models.page_information import PageInformation


class GoogleSearchDTO(BaseModel):
    query: str
    country: Optional[str] = None
    filter_results_prompt: Optional[str] = None
    page_information: PageInformation
    llm_config: LLMConfig
