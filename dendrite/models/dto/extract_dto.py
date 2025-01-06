import json
from typing import Any, Optional

from pydantic import BaseModel

from dendrite.models.page_information import PageInformation


class ExtractDTO(BaseModel):
    page_information: PageInformation
    prompt: str

    return_data_json_schema: Any
    use_screenshot: bool = False

    @property
    def combined_prompt(self) -> str:

        json_schema_prompt = (
            ""
            if self.return_data_json_schema == None
            else f"\nJson schema: {json.dumps(self.return_data_json_schema)}"
        )
        return f"Task: {self.prompt}{json_schema_prompt}"
