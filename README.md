# Dendrite

Dendrite is a developer tool that makes it very easy to interact with and scrape websites using AI.

This project is still in it's infancy and is susceptible to many changes the coming months.

If you want to chat with us developers, give feedback and report bugs, our discord is the place to be! [Invite link](https://discord.gg/ETPBdXU3kx)

## Installation:

```
pip install dendrite-python-sdk && playwright install
```

## Getting started:

Here is a very simple example of how to use Dendrite. In the example we go to google.com, find the search bar and enter 'hello world' into it.

```python
from dendrite_python_sdk import DendriteBrowser
import asyncio

async def main():
    dendrite_browser = DendriteBrowser(openai_api_key=...)
    page = await dendrite_browser.goto("https://google.com")
    search_bar = await page.get_interactable_element("Return the search bar")
    await search_bar.fill("hello world")
    dendrite_browser.close()

asyncio.run(main())
```

More robust documentation is coming soon. For now if you get stuck, don't be shy to join our [discord server](https://discord.gg/ETPBdXU3kx) and ask questions!

## More Advanced Example:

By providing an OpenAI API key you can use `DendriteBrowser` to interact with and extract data from websites with prompts instead of needing to find all the correct selectors.

Here's an example (See more examples in `dendrite_python_sdk/examples`):

```python
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
```
