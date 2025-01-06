import time
import time
from typing import Generic, Optional, Type, TypeVar
from playwright.sync_api import Download, FileChooser, Page

Events = TypeVar("Events", Download, FileChooser)
mapping = {Download: "download", FileChooser: "filechooser"}


class EventSync(Generic[Events]):

    def __init__(self, event_type: Type[Events]):
        self.event_type = event_type
        self.event_set = False
        self.data: Optional[Events] = None

    def get_data(self, pw_page: Page, timeout: float = 30000) -> Events:
        start_time = time.time()
        while not self.event_set:
            elapsed_time = (time.time() - start_time) * 1000
            if elapsed_time > timeout:
                raise TimeoutError(f'Timeout waiting for event "{self.event_type}".')
            pw_page.wait_for_timeout(0)
            time.sleep(0.01)
        data = self.data
        self.data = None
        self.event_set = False
        if data is None:
            raise ValueError("Data is None for event type: ", self.event_type)
        return data

    def set_event(self, data: Events) -> None:
        """
        Sets the event and stores the provided data.

        This method is used to signal that the data is ready to be retrieved by any waiting tasks.

        Args:
            data (T): The data to be stored and associated with the event.

        Returns:
            None
        """
        self.data = data
        self.event_set = True
