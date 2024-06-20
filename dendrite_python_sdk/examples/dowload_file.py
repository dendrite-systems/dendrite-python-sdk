import os
import asyncio

from dendrite_python_sdk import DendriteRemoteBrowser, DendriteBrowser
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


async def main(username: str):
    dendrite_browser = DendriteRemoteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", "")
    )

    page = await dendrite_browser.goto(
        "https://browser-tests-alpha.vercel.app/api/download-test", scroll_through_entire_page=False
    )

    # download = await page.get_playwright_page().wait_for_selector("#download")

    # Get elements with prompts instead of using brittle selectors
    download = await page.get_interactable_element("The link for downloading the file.")
    
    client = await page.dendrite_browser.browser_context.new_cdp_session(page.get_playwright_page()) # type: ignore


    await client.send("Browser.setDownloadBehavior",{
        "behavior": "allow",
        "downloadPath": "downloads",
        "eventsEnabled": True,
    })

    async with page.get_playwright_page().expect_download() as download_info:
        await download.click()
    # await page.dendrite_browser.get_download()
    download = await download_info.value
    failed = await download.failure()

    if failed:
        print("Download failed")
        raise Exception("Download failed")
    
    print(f"Suggested file name: {download.suggested_filename}")
    # print(f"Download path: {await download.path()}")
    # await download.save_as("downloads/" + download.suggested_filename)

# Wait for the download process to complete and save the downloaded file somewhere
    # await download.save_as("testing/" + download.suggested_filename)


    # HACK: Enough time to solve recaptcha
    await asyncio.sleep(30)


asyncio.run(main("coffecup25"))
