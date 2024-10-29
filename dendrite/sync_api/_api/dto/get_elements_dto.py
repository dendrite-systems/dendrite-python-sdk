from typing import Dict, Union
from pydantic import BaseModel
from dendrite.sync_api._core.models.api_config import APIConfig
from dendrite.sync_api._core.models.page_information import PageInformation


class CheckSelectorCacheDTO(BaseModel):
    url: str
    prompt: Union[str, Dict[str, str]]


class GetElementsDTO(BaseModel):
    page_information: PageInformation
    prompt: Union[str, Dict[str, str]]
    api_config: APIConfig
    use_cache: bool = True
    only_one: bool
    force_use_cache: bool = False
