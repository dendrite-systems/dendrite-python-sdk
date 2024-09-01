from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union
from playwright.async_api import Download


class DownloadInterface(ABC):
    def __init__(self, download: Download):
        self._download = download

    @abstractmethod
    async def save_as(self, path: Union[str, Path]) -> None:
        pass

    @property
    def url(self) -> str:
        return self._download.url

    @property
    def suggested_filename(self) -> str:
        return self._download.suggested_filename

    async def failure(self):
        return await self._download.failure()
