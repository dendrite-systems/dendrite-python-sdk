from typing import List, Optional

from pydantic import BaseModel

from dendrite_sdk.async_api._common.status import Status


class GetElementResponse(BaseModel):
    status: Status
    selectors: Optional[List[str]] = None
    message: str = ""
