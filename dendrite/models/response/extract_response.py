from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

from dendrite.browser._common.types import Status

T = TypeVar("T")


class ExtractResponse(BaseModel, Generic[T]):
    status: Status
    message: str
    return_data: Optional[T] = None
    created_script: Optional[str] = None
