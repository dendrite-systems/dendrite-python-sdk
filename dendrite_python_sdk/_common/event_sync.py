import asyncio
from typing import Generic, Optional, TypeVar


T = TypeVar("T")


class EventSync(Generic[T]):
    def __init__(self) -> None:
        self.event = asyncio.Event()
        self.data: Optional[T] = None

    def set_event(self, data: T) -> None:
        self.data = data
        self.event.set()

    async def get_data(self, timeout: float = 30) -> T:
        try:
            await asyncio.wait_for(self.event.wait(), timeout)
            if not self.data:
                raise Exception(f"No {self.data.__class__.__name__} was found.")
            data = self.data

            self.data = None
            self.event.clear()
            return data
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"There was no {self.data.__class__.__name__} event set within the specified timeout."
            )
