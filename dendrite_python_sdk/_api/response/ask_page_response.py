from typing import Generic, TypeVar
from pydantic import BaseModel


T = TypeVar("T")


class AskPageResponse(BaseModel, Generic[T]):
    return_data: T
    description: str
