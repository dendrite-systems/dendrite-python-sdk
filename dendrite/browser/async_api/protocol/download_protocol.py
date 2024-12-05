from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Union

from playwright.async_api import Download


class DownloadInterface(ABC, Download):
    def __init__(self, download: Download):
        self._download = download

    def __getattribute__(self, name: str) -> Any:
        # First, check if DownloadInterface has the attribute
        try:
            return super().__getattribute__(name)
        except AttributeError:
            # If not, delegate to the wrapped Download instance
            return getattr(self._download, name)

    @abstractmethod
    async def save_as(self, path: Union[str, Path]) -> None:
        pass
