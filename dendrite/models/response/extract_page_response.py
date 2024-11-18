from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel
from dendrite.browser._common.types import Status


T = TypeVar("T")


class ExtractPageResponse(BaseModel, Generic[T]):
    return_data: T
    message: str
    created_script: Optional[str] = None
    status: Status
    used_cache: bool
