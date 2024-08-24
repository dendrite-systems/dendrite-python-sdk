import json
from typing import Any, Optional
from pydantic import BaseModel
from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.models.PageInformation import PageInformation


class TryRunScriptDTO(BaseModel):
    url: str
    raw_html: str
    llm_config: LLMConfig
    prompt: str
    db_prompt: Optional[str] = (
        None  # If you wish to cache a script based of a fixed prompt use this value
    )
    return_data_json_schema: Any
