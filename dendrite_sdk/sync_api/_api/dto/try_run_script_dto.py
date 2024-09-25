from typing import Any, Optional
from pydantic import BaseModel
from dendrite_sdk.sync_api._core.models.llm_config import LLMConfig


class TryRunScriptDTO(BaseModel):
    url: str
    raw_html: str
    llm_config: LLMConfig
    prompt: str
    db_prompt: Optional[str] = None
    return_data_json_schema: Any
