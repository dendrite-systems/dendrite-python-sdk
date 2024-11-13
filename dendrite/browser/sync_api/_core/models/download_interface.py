from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Union
from playwright.sync_api import Download


class DownloadInterface(ABC, Download):

    def __init__(self, download: Download):
        self._download = download

    def __getattribute__(self, name: str) -> Any:
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return getattr(self._download, name)

    @abstractmethod
    def save_as(self, path: Union[str, Path]) -> None:
        pass
