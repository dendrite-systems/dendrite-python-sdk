
from typing import Protocol, Union, overload

from typing import Protocol, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class CacheProtocol(Protocol, Generic[T]):

    @overload
    def get(self, key: dict) -> Union[T, None]:
        ...
    @overload
    def get(self, key: str) -> Union[T, None]:
        ...
    def get(self, key: Union[str,dict]) -> Union[T, None]:
        ...

    def set(self, key: str, value: T) -> None:
        ...

    def delete(self, key: str) -> None:
        ...