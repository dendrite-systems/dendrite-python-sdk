from typing import Any, Optional
from pydantic import BaseModel
from dendrite.async_api._core.models.api_config import APIConfig


class TryRunScriptDTO(BaseModel):
    url: str
    raw_html: str
    api_config: APIConfig
    prompt: str
    db_prompt: Optional[str] = (
        None  # If you wish to cache a script based of a fixed prompt use this value
    )
    return_data_json_schema: Any
