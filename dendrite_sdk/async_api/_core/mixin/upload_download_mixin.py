import pathlib
from typing import Sequence, Union

from playwright.async_api import (
    Download,
    FilePayload,
)
from dendrite_sdk.async_api._core.protocol.page_protocol import DendritePageProtocol


class DownloadUploadMixin(DendritePageProtocol):

    async def get_download(self, timeout: float = 30000) -> Download:
        """
        Gets the most recent download from the browser.

        Args:
            timeout (float, optional): The maximum amount of time (in milliseconds) to wait for the download to complete. Defaults to 30.

        Returns:
            The downloaded file data.
        """
        browser = self._get_dendrite_browser()
        page = await self._get_page()
        download = await browser._get_download(page.playwright_page, timeout)
        return download

    async def upload_files(
        self,
        files: Union[
            str,
            pathlib.Path,
            FilePayload,
            Sequence[Union[str, pathlib.Path]],
            Sequence[FilePayload],
        ],
        timeout: float = 30000,
    ) -> None:
        """
        Uploads files to the page using a file chooser.

        Args:
            files (Union[str, pathlib.Path, FilePayload, Sequence[Union[str, pathlib.Path]], Sequence[FilePayload]]): The file(s) to be uploaded.
                This can be a file path, a `FilePayload` object, or a sequence of file paths or `FilePayload` objects.
            timeout (float, optional): The maximum amount of time (in milliseconds) to wait for the file chooser to be ready. Defaults to 30.

        Returns:
            None
        """
        browser = self._get_dendrite_browser()
        page = await self._get_page()
        file_chooser = await browser._get_filechooser(page.playwright_page, timeout)
        await file_chooser.set_files(files)
