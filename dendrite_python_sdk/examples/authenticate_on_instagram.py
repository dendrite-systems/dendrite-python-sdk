import asyncio
from dendrite_python_sdk import DendriteBrowser


async def authenticate_on_instagram():
    dendrite_browser = DendriteBrowser()
    await dendrite_browser.authenticate("instagram.com")
    page = await dendrite_browser.goto(
        "https://instagram.com",
        expected_page="You should be logged in with the instagram feed visible",
    )
    res = await page.ask("Describe the first post in my feed")
    print("First post description: ", res.return_data)


asyncio.run(authenticate_on_instagram())
