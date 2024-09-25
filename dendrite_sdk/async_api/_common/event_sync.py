import asyncio
from typing import Generic, Optional, Type, TypeVar, Union, cast
import playwright
from playwright.async_api import Page, Download, FileChooser
import playwright.sync_api


Events = TypeVar("Events", Download, FileChooser)

mapping = {
    Download: "download",
    FileChooser: "filechooser",
}


class EventSync(Generic[Events]):
    def __init__(self, event_type: Type[Events]):
        self.event_type = event_type

    async def get_data(self, pw_page: Page, timeout: float = 30000) -> Events:
        try:
            data = await pw_page.wait_for_event(
                mapping[self.event_type], timeout=timeout
            )
            this_type = self.event_type
            return cast(this_type, data)

        except playwright.sync_api.TimeoutError:
            raise TimeoutError(
                f"There was no '{self.event_type}' event set within the specified timeout."
            )
