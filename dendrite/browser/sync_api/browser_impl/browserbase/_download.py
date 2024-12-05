import re
import shutil
import zipfile
from pathlib import Path
from typing import Union
from loguru import logger
from playwright.sync_api import Download
from dendrite.browser.sync_api.browser_impl.browserbase._client import BrowserbaseClient
from dendrite.browser.sync_api.protocol.download_protocol import DownloadInterface


class BrowserbaseDownload(DownloadInterface):

    def __init__(
        self, session_id: str, download: Download, client: BrowserbaseClient
    ) -> None:
        super().__init__(download)
        self._session_id = session_id
        self._client = client

    def save_as(self, path: Union[str, Path], timeout: float = 20) -> None:
        """
        Save the latest file from the downloaded ZIP archive to the specified path.

        Args:
            path (Union[str, Path]): The destination file path where the latest file will be saved.
            timeout (float, optional): Timeout for the save operation. Defaults to 20 seconds.

        Raises:
            Exception: If no matching files are found in the ZIP archive or if the file cannot be saved.
        """
        destination_path = Path(path)
        source_path = self._download.path()
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source_path, "r") as zip_ref:
            file_list = zip_ref.namelist()
            sorted_files = sorted(file_list, key=extract_timestamp, reverse=True)
            if not sorted_files:
                raise FileNotFoundError(
                    "No files found in the Browserbase download ZIP"
                )
            latest_file = sorted_files[0]
            with zip_ref.open(latest_file) as source, open(
                destination_path, "wb"
            ) as target:
                shutil.copyfileobj(source, target)
        logger.info(f"Latest file saved successfully to {destination_path}")


def extract_timestamp(filename):
    timestamp_pattern = re.compile("-(\\d+)\\.")
    match = timestamp_pattern.search(filename)
    return int(match.group(1)) if match else 0
