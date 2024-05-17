from typing import Any
from pydantic import BaseModel

from dendrite_python_sdk.dendrite_browser.common.status import Status


class ScrapePageResponse(BaseModel):
    json_data: Any
    message: str
    status: Status
