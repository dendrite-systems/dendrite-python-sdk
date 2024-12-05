from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class AskPageResponse(BaseModel, Generic[T]):
    status: Literal["success", "error"]
    return_data: T
    description: str
