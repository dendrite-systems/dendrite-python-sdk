import asyncio
import os
from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv
from dendrite_python_sdk.exceptions.DendriteException import DendriteException
from dendrite_python_sdk.exceptions.IncorrectOutcomeException import (
    IncorrectOutcomeException,
)

from dendrite_python_sdk.models.LLMConfig import LLMConfig

load_dotenv(find_dotenv())

openai_api_key = os.environ.get("OPENAI_API_KEY", "")

llm_config = LLMConfig(openai_api_key=openai_api_key)
dendrite_browser = DendriteBrowser(
    llm_config=llm_config, playwright_options={"headless": False}
)


async def run():
    try:
        await dendrite_browser.launch()
        # search_results = await dendrite_browser.google_search(
        #     "Fishards official website", "only the official website"
        # )
        # print("search_results: ", search_results)
        # await asyncio.sleep(4)

        page = await dendrite_browser.goto("https://fishards.com")
        element = await page.get_interactable_element("Get the epic lollol button")
        res = await element.click(
            timeout=1000,
            expected_outcome="Should redirect to Fishards twitter page, not steam page",
        )
        print("res: ", res)

        page = await dendrite_browser.get_active_page()
        res = await page.scrape(
            prompt="Get the developers name and url page",
            return_data_json_schema={
                "type": "object",
                "parameters": {"url": {"type": "string"}, "name": {"type": "string"}},
            },
        )
        print("data res: ", res)
        search_bar = await page.get_interactable_element(
            "The search bar with the placeholder text 'search'"
        )
        fill_res = await search_bar.fill("Fishards")
        print("fill_res: ", fill_res)
        await page.get_playwright_page().keyboard.press("Enter")
        await asyncio.sleep(4)
        await dendrite_browser.close()
    except IncorrectOutcomeException as e:
        print("Incorrect expected outcome! ", e.message)
    except DendriteException as e:
        print(e.message)


asyncio.run(run())
