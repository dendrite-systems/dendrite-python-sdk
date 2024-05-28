import os
from dendrite_python_sdk import DendriteBrowser
import asyncio
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


async def main():
    # Launch browser locally
    dendrite_browser = DendriteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", "")
    )

    # Go to google.com
    page = await dendrite_browser.goto("https://google.com")

    # Get the reject cookies button
    close_cookies = await page.get_interactable_element("reject cookies popup button")

    # Click the button, returns IncorrectOutcomeException if the popup wasn't closed
    await close_cookies.click(expected_outcome="That the cookies popup closed.")

    # Get the search bar
    search_bar = await page.get_interactable_element("Return the search bar")

    # Enter "hello world" into it.
    await search_bar.fill(
        "hello world", expected_outcome="The words 'hello world' to have been entered"
    )

    # Use the Playwright page to press enter.
    await page.get_playwright_page().keyboard.press("Enter")

    await asyncio.sleep(2)
    await dendrite_browser.close()


asyncio.run(main())
