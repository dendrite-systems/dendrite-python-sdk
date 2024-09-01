from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

from dendrite_sdk._common.status import Status


T = TypeVar("T")


class ScrapePageResponse(BaseModel, Generic[T]):
    return_data: T
    message: str
    created_script: Optional[str] = None
    status: Status
    used_cache: bool
