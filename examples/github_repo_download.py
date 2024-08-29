import asyncio
from dotenv import load_dotenv, find_dotenv

from dendrite_python_sdk.ext.browserbase import BrowserBaseBrowser


load_dotenv(find_dotenv())


async def main(username: str):
    try:
        dendrite_browser = BrowserBaseBrowser(enable_downloads=True)

        page = await dendrite_browser.goto(
            "https://github.com/dendrite-agent/dendrite-python-sdk"
        )

        # Get elements with prompts instead of using brittle selectors
        email_field = await page.get_element(
            "The code button for downloading the repo", max_retries=1
        )
        print(email_field.locator)
        await email_field.highlight()
        await email_field.click()

        zip = await page.get_element("The zip download option", use_cache=False)
        await zip.highlight()
        input("Press Enter to continue...")
        await zip.click()

        dw = await page.get_download()

        if fail := await dw.failure():
            print(f"Download failed: {fail}")

        await dw.save_as("dendrite-python-sdk.zip")

    finally:
        await dendrite_browser.close()

    # await page.keyboard.press("Enter")

    # first_email = await page.get_element("The first email in the inbox.")
    # await first_email.hover()

    # dw =  await page.get_download()

    # HACK: Enough time to solve recaptcha
    await asyncio.sleep(20)


asyncio.run(main("coffecup25"))
