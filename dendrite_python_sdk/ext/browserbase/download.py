from pathlib import Path
from playwright.async_api import Download

from dendrite_python_sdk._core.models.download_interface import DownloadInterface
from dendrite_python_sdk.ext.browser_base._client import save_downloads_on_disk


class BrowserBaseDownload(DownloadInterface):
    def __init__(self, session_id: str, download: Download):
        super().__init__(download)
        self._session_id = session_id

    async def save_as(self, path: str | Path) -> None:
        """
        Downloads all of the downloaded files to a specified path on disk.
        The files are returned in a zip file at the specified path.
        If the path points to a directory, the zip file will be saved in that directory as downloads.zip
        """
        await save_downloads_on_disk(self._session_id, path, 60)