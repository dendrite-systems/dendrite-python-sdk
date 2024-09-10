import asyncio
from typing import Generic, Optional, TypeVar

from dendrite_sdk._exceptions.dendrite_exception import DendriteException


T = TypeVar("T")


class EventSync(Generic[T]):
    """
    EventSync is a synchronization utility class that allows for setting and retrieving data
    across asynchronous tasks using an asyncio event. The class is generic and can be used with
    any data type.

    This class is useful for scenarios where one task needs to wait for data to be provided
    by another task, with support for timeouts.

    Attributes:
        event (asyncio.Event): The asyncio event that signals when data is ready to be retrieved.
        data (Optional[T]): The data associated with the event, of a generic type `T`.

    Methods:
        set_event(data: T) -> None:
            Sets the event and stores the provided data.

        get_data(timeout: float = 30000) -> T:
            Waits for the event to be set and retrieves the associated data, with an optional timeout.
    """

    def __init__(self) -> None:
        self.event = asyncio.Event()
        self.data: Optional[T] = None

    def set_event(self, data: T) -> None:
        """
        Sets the event and stores the provided data.

        This method is used to signal that the data is ready to be retrieved by any waiting tasks.

        Args:
            data (T): The data to be stored and associated with the event.

        Returns:
            None
        """
        self.data = data
        self.event.set()

    async def get_data(self, timeout: float = 30000) -> T:
        """
        Waits for the event to be set and retrieves the associated data.

        This method waits for the event to be set by another task and then returns the stored data.
        If the event is not set within the specified timeout, a TimeoutError is raised.

        Args:
            timeout (float, optional): The maximum time (in milliseconds) to wait for the event to be set. Defaults to 30000.

        Returns:
            T: The data associated with the event.

        Raises:
            TimeoutError: If the event is not set within the specified timeout.
            Exception: If the event is set but no data is available.
        """
        try:
            await asyncio.wait_for(self.event.wait(), timeout * 0.001)
            if not self.data:
                raise DendriteException(f"No {self.data.__class__.__name__} was found.")
            data = self.data

            self.data = None
            self.event.clear()
            return data
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"There was no {self.data.__class__.__name__} event set within the specified timeout."
            )
