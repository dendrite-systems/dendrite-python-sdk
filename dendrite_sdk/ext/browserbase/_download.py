from pathlib import Path
from typing import Union
from loguru import logger
from playwright.async_api import Download

from dendrite_sdk._core.models.download_interface import DownloadInterface
from dendrite_sdk.ext.browserbase._client import BrowserBaseClient


class BrowserBaseDownload(DownloadInterface):
    def __init__(
        self, session_id: str, download: Download, client: BrowserBaseClient
    ) -> None:
        super().__init__(download)
        self._session_id = session_id
        self._client = client

    async def save_as(self, path: Union[str, Path], timeout: float = 20) -> None:
        """
        Downloads all of the downloaded files to a specified path on disk.
        The files are returned in a zip file at the specified path.
        If the path points to a directory, the zip file will be saved in that directory as downloads.zip
        """
        logger.info(f"Saving downloads to {path}")
        await self._client.save_downloads_on_disk(self._session_id, path, timeout)
