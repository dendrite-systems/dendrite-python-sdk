import os
import asyncio

from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


async def main(game_to_extract: str):
    dendrite_browser = DendriteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        dendrite_api_key=os.environ.get("DENDRITE_API_KEY", ""),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )

    page = await dendrite_browser.goto(
        f"https://store.steampowered.com/search/?sort_by=_ASC&term={game_to_extract}&supportedlang=english",
        scroll_through_entire_page=False,
    )

    url = await page.scrape(
        "Get the URL of first listed search result and return it like this: {url: str}"
    )

    print(url.json_data["url"])


asyncio.run(main("fishards"))
