# Dendrite

With Dendrite you can interact with and scrape websites using prompts instead of selectors:

```python
startup_urls = await page.scrape("Extract a list of valid urls for each listed startup's YC page")
```

Join our discord to give feedback and report bugs! [Invite link](https://discord.gg/ETPBdXU3kx)


## Installation:

You'll need `dendrite-python-sdk`, `asyncio` and `playwright`. You'll also need to install the browser drivers with `playwright install`.

Ensure you have Python 3.9 or later installed.

pip:
```
pip install asyncio playwright dendrite-python-sdk
playwright install
```

poetry:
```
poetry add asyncio playwright dendrite-python-sdk
poetry run playwright install
```

## Quick start:

Here is a very simple example of how to use Dendrite.

Install dendrite and asyncio like so: `pip install asyncio dendrite-python-sdk && playwright install` and create a file called `main.py`. Use the code below and run it with `python main.py` from the terminal.

`main.py`
```python
from dendrite_python_sdk import DendriteBrowser
import asyncio

async def main():
    # Launch browser locally
    dendrite_browser = DendriteBrowser(openai_api_key=...) # Use your OpenAI key here

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
```

## More Advanced Example:

With Dendrite we can do more than just finding and using elements. 

We can scrape data from pages and ensure that the returned data followed a certain structure by prompting, using a JSON schema or passing in a pydantic model.

Below is an example of how he can, see more examples in `dendrite_python_sdk/examples` or [on our website](https://dendrite.se/#example-code).

```python
import os
import asyncio

from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv
import pandas as pd

load_dotenv(find_dotenv())


async def main():
    dendrite_browser = DendriteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        dendrite_api_key=os.environ.get("DENDRITE_API_KEY", "") # Generate a dendrite API at https://dendrite.se to get better rate limits and latency.
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


## Class Documentation

### DendriteBrowser

DendriteBrowser is an abstraction on top of playwright's browser. You can do everything you would normally do with Playwright but with a few new handy AI functions. Access 

#### Methods



**`__init__(self, openai_api_key: str, id=None, playwright_options: Any = {"headless": False})`**  

Initializes the DendriteBrowser class.

**Params**:
- `openai_api_key` (str): Your OpenAI API Key.
- `id` (Optional): The unique ID for the browser session.
- `playwright_options` (dict): Options to configure Playwright browser.




**`get_active_page(self) -> DendritePage`**  

Returns the active page.




**`goto(self, url: str, scroll_through_entire_page: Optional[bool] = True) -> DendritePage`**  

Navigates to the specified URL. 

**Params**:
- `url` (str): URL of the webpage.
- `scroll_through_entire_page` (Optional[bool]): Whether to scroll through the entire page.




**`google_search(self, query: str, filter_results_prompt: Optional[str] = None, load_all_results: Optional[bool] = True) -> List[SearchResult]`**  

Performs a Google search and returns search results.

**Params**:
- `query` (str): The search query.
- `filter_results_prompt` (Optional[str]): Prompt to filter results.
- `load_all_results` (Optional[bool]): Whether to load all results.




**`new_page(self) -> DendritePage`**  

Opens a new page in the browser.




**`close(self)`**  

Closes the browser context.



### DendritePage

Abstraction layer on top of Playwright's Page class. Use `get_playwright_locator` to get the playwright page.

#### Methods



**`get_playwright_page(self) -> Page`**  

Returns the Playwright page instance.




**`scrape(self, prompt: str, expected_return_data: Optional[str] = None, return_data_json_schema: Optional[Any] = None, pydantic_return_model: Optional[Type[BaseModel]] = None) -> Any`**  

Scrapes data from the page based on a prompt.

**Params**:
- `prompt` (str): The prompt to gather data.
- `expected_return_data` (Optional[str]): Expected return data.
- `return_data_json_schema` (Optional[Any]): JSON schema for return data.
- `pydantic_return_model` (Optional[Type[BaseModel]]): Pydantic model for return data.




**`scroll_through_entire_page(self) -> None`**  

Scrolls through the entire page.




**`get_interactable_element(self, prompt: str) -> DendriteLocator`**  

Returns an interactable element based on a prompt.


### DendriteLocator

Abstraction layer on top of Playwright's Locator class. Use `get_playwright_locator` to get the playwright locator.

#### Methods



**`get_playwright_locator(self) -> Locator`**  

Returns the Playwright locator.




**`wait_for_page_changes(self, old_url: str, timeout: float = 2)`**  

Waits for changes in the page.
**Params**:

- `old_url` (str): The URL before the interaction.
- `timeout` (float): The time to wait for changes.




**`click(self, expected_outcome="", *args, **kwargs) -> InteractionResponse`**  

Clicks the element and handles the interaction.

**Params**:
- `expected_outcome` (str): Expected outcome after clicking.




**`fill(self, value: str, expected_outcome="", *args, **kwargs)`**  

Fills the element with the provided value.

**Params**:
- `value` (str): The value to fill.
- `expected_outcome` (str): Expected outcome after filling.

