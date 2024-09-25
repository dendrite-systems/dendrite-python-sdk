from pydantic import BaseModel

from dendrite_sdk._core.models.api_config import APIConfig
from dendrite_sdk._core.models.page_information import PageInformation


class GetInteractionDTO(BaseModel):
    page_information: PageInformation
    api_config: APIConfig
    prompt: str
