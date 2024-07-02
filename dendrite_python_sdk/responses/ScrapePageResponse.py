from typing import Any, List, Optional
from pydantic import BaseModel

from dendrite_python_sdk.dendrite_browser.common.status import Status


class ScrapePageResponse(BaseModel):
    json_data: Any
    message: str
    created_script: Optional[str] = None
    status: Status
    used_cache: bool
