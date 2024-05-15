# dendrite-python-sdk

This project is in it's infancy and has been built quickly to allow for fast iteration. Contribution from more seasoned open source pros would be much appreciated! 

## Installation:

```
pip install dendrite-python-sdk
```

## Example:

By providing an OpenAI API key you can use `DendriteBrowser` to interact with and extract data from websites with prompts instead of needing to find all the correct selectors.

`DendriteBrowser` uses playwright under the hood to load and interact with websites.

Here's an example (See more examples in `dendrite_python_sdk/examples`):

```python
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
    # Go to fishards.com
    page = await dendrite_browser.goto("https://fishards.com")

    # Here we get the desired element by describing it with a prompt on the page we navigated to
    element = await page.get_interactable_element("Get the try for free button")
    
    # By providing the expected_outcome argument, the response payload will contain a status of 'success' or 'failed', along with a message describing what when right or wrong
    res = await element.click(
        timeout=1000, expected_outcome="Should redirect to Fishards Steam page"
    )
    print("res: ", res)

    # Now that we redirected, lets get the active page and search for fishards in the search bar
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
```