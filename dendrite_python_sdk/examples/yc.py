import os
import asyncio

from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv
import pandas as pd

load_dotenv(find_dotenv())


async def main():
    dendrite_browser = DendriteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", "")
    )

    page = await dendrite_browser.goto(
        "https://ycombinator.com/companies", scroll_through_entire_page=False
    )

    # Get elements with prompts instead of using brittle selectors
    search_bar = await page.get_interactable_element(
        "The search bar used to find startups"
    )
    await search_bar.fill("AI agent")

    # Scraping data is as easy as writing a good prompt
    await page.scroll_through_entire_page()
    startup_urls = await page.scrape(
        "Extract a list of valid urls for each listed startup's YC page"
    )

    # Let's go to every AI agent startup's page and fetch information about the founders
    startup_info = []
    for url in startup_urls:
        page = await dendrite_browser.goto(url)
        startup_details = await page.scrape(
            "Extract a dict like this: {name: str, slogan: str, founders_social_media_urls: a string where each url is separated by a linebreak}"
        )
        print("startup_details: ", startup_details)
        startup_info.append(startup_details)

    df = pd.DataFrame(startup_info)
    df.to_excel("ai_agent_founders.xlsx", index=False)


asyncio.run(main())
