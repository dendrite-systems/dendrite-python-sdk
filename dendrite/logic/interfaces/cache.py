from typing import Generic, Protocol, TypeVar, Union, overload

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)
