import asyncio
import os
from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv

from dendrite_python_sdk.models.LLMConfig import LLMConfig

load_dotenv(find_dotenv())

openai_api_key = os.environ.get("OPENAI_API_KEY", "")

llm_config = LLMConfig(openai_api_key=openai_api_key)
dendrite_browser = DendriteBrowser(
    llm_config=llm_config, playwright_options={"headless": False}
)


async def run():
    await dendrite_browser.launch()
    page = await dendrite_browser.goto("https://fishards.com")
    element = await page.get_interactable_element("Get the try for free button")
    res = await element.click(
        timeout=1000, expected_outcome="Should redirect to Fishards Steam page"
    )
    print("res: ", res)
    page = await dendrite_browser.get_active_page()
    search_bar = await page.get_interactable_element(
        "The search bar with the placeholder text 'search'"
    )
    fill_res = await search_bar.fill("Fishards")
    print("fill_res: ", fill_res)
    await page.page.keyboard.press("Enter")
    await asyncio.sleep(4)
    await dendrite_browser.close()


asyncio.run(run())
