import os
import asyncio

from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


async def main(username: str):
    dendrite_browser = DendriteBrowser(
        dendrite_api_key=os.environ.get("DENDRITE_API_KEY", ""),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
    )

    await dendrite_browser.launch("coffecup25", "gmail.com")
    page = await dendrite_browser.goto(
        "https://mail.google.com/mail/u/1/#inbox", scroll_through_entire_page=False
    )

    input()


asyncio.run(main("coffecup25"))
