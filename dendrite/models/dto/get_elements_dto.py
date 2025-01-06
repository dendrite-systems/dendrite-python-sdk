from typing import Dict, Union

from pydantic import BaseModel

from dendrite.models.page_information import PageInformation


class CheckSelectorCacheDTO(BaseModel):
    url: str
    prompt: Union[str, Dict[str, str]]


class GetElementsDTO(BaseModel):
    prompt: Union[str, Dict[str, str]]
    page_information: PageInformation
    only_one: bool
