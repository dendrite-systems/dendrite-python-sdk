from typing import Optional
from pydantic import BaseModel
from dendrite.sync_api._core.models.api_config import APIConfig
from dendrite.sync_api._core.models.page_information import PageInformation


class GoogleSearchDTO(BaseModel):
    query: str
    country: Optional[str] = None
    filter_results_prompt: Optional[str] = None
    page_information: PageInformation
    api_config: APIConfig
