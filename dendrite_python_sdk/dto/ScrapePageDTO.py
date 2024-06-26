from typing import Any, Optional
from pydantic import BaseModel

from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.models.PageInformation import PageInformation


class ScrapePageDTO(BaseModel):
    page_information: PageInformation
    llm_config: LLMConfig
    prompt: str
    db_prompt: Optional[str] = (
        None  # If you wish to cache a script based of a fixed prompt use this value
    )
    expected_return_data: Optional[str]
    return_data_json_schema: Any
    use_screenshot: bool = False
