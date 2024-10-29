import os
import pytest
from dendrite.async_api._core.dendrite_browser import AsyncDendrite


@pytest.mark.asyncio(loop_scope="session")
async def test_download(browserbase: AsyncDendrite, tmp_path):
    page = await browserbase.goto(
        "https://browser-tests-alpha.vercel.app/api/download-test"
    )
    await page.playwright_page.get_by_text("Download File").click()
    dw = await page.get_download(timeout=5000)

    # Save the downloaded file to the suggested location
    download_path = tmp_path / dw.suggested_filename
    await dw.save_as(download_path)

    # Assertion: Verify that the file was downloaded successfully
    assert (
        download_path.exists()
    ), f"Expected downloaded file at {download_path}, but it does not exist."
    assert (
        os.path.getsize(download_path) > 0
    ), f"Expected non-empty file at {download_path}, but file size is zero."
