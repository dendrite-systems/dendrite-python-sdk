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
    expected_return_data: Optional[str]
    return_data_json_schema: Any

    @property
    def combined_prompt(self) -> str:
        expected_return_data_prompt = (
            ""
            if self.expected_return_data == None
            else f"\nExpected return data: {self.expected_return_data}"
        )
        json_schema_prompt = (
            ""
            if self.return_data_json_schema == None
            else f"\nJson schema: {json.dumps(self.return_data_json_schema)}"
        )
        return f"Task: {self.prompt}{expected_return_data_prompt}{json_schema_prompt}"
