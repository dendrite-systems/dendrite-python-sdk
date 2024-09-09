from pathlib import Path
import re
import shutil
from typing import Union
import zipfile
from loguru import logger
from playwright.async_api import Download

from dendrite_sdk._core.models.download_interface import DownloadInterface
from dendrite_sdk.ext.browserbase._client import BrowserbaseClient


class BrowserbaseDownload(DownloadInterface):
    def __init__(
        self, session_id: str, download: Download, client: BrowserbaseClient
    ) -> None:
        super().__init__(download)
        self._session_id = session_id
        self._client = client

    async def save_as(self, path: Union[str, Path], timeout: float = 20) -> None:
        """
        Save the latest file from the downloaded ZIP archive to the specified path.

        Args:
            path (Union[str, Path]): The destination file path where the latest file will be saved.
            timeout (float, optional): Timeout for the save operation. Defaults to 20 seconds.

        Raises:
            Exception: If no matching files are found in the ZIP archive or if the file cannot be saved.
        """

        destination_path = Path(path)

        source_path = await self._download.path()
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(source_path, "r") as zip_ref:
            # Get all file names in the ZIP
            file_list = zip_ref.namelist()

            # Filter and sort files based on timestamp
            timestamp_pattern = re.compile(r"-(\d+)\.")
            sorted_files = sorted(
                file_list,
                key=lambda x: int(
                    timestamp_pattern.search(x).group(1)  # type: ignore
                    if timestamp_pattern.search(x)
                    else 0
                ),
                reverse=True,
            )

            if not sorted_files:
                raise FileNotFoundError(
                    "No files found in the Browserbase download ZIP"
                )

            # Extract the latest file
            latest_file = sorted_files[0]
            with zip_ref.open(latest_file) as source, open(
                destination_path, "wb"
            ) as target:
                shutil.copyfileobj(source, target)
        logger.info(f"Latest file saved successfully to {destination_path}")
