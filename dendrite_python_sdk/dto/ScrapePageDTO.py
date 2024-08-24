import json
from typing import Any, List, Optional
from pydantic import BaseModel
from dendrite_python_sdk.models.LLMConfig import LLMConfig

from dendrite_python_sdk.models.PageInformation import PageInformation


class ScrapePageDTO(BaseModel):
    page_information: PageInformation
    llm_config: LLMConfig
    prompt: str
    return_data_json_schema: Any
    use_screenshot: bool = False
    use_cache: bool = True
    force_use_cache: bool = False

    @property
    def combined_prompt(self) -> str:

        json_schema_prompt = (
            ""
            if self.return_data_json_schema == None
            else f"\nJson schema: {json.dumps(self.return_data_json_schema)}"
        )
        return f"Task: {self.prompt}{json_schema_prompt}"
