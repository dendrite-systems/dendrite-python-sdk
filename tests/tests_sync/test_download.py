# content of test_tmp_path.py
import os
from dendrite_sdk.sync_api import Dendrite


def test_download(dendrite_browser: Dendrite, tmp_path):
    page = dendrite_browser.goto(
        "https://browser-tests-alpha.vercel.app/api/download-test"
    )
    page.playwright_page.get_by_text("Download File").click()
    dw = page.get_download(timeout=5000)
    dw.save_as(dw.suggested_filename)

    # Save the downloaded file to the suggested location
    download_path = tmp_path / dw.suggested_filename
    dw.save_as(download_path)

    # Assertion: Verify that the file was downloaded successfully
    assert (
        download_path.exists()
    ), f"Expected downloaded file at {download_path}, but it does not exist."
    assert (
        os.path.getsize(download_path) > 0
    ), f"Expected non-empty file at {download_path}, but file size is zero."
