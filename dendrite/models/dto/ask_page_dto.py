from typing import Any, Optional

from pydantic import BaseModel

from dendrite.models.page_information import PageInformation


class AskPageDTO(BaseModel):
    prompt: str
    return_schema: Optional[Any]
    page_information: PageInformation
