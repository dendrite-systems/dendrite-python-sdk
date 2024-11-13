from typing import Any, Optional
from pydantic import BaseModel
from dendrite.browser.sync_api._core.models.api_config import APIConfig


class TryRunScriptDTO(BaseModel):
    url: str
    raw_html: str
    api_config: APIConfig
    prompt: str
    db_prompt: Optional[str] = None
    return_data_json_schema: Any
