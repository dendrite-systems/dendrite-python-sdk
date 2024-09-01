# Dendrite

[Read the full docs here](https://docs.dendrite.systems)

## What is Dendrite?

Dendrite is a suite of tools that makes it easy to create web integrations for AI agents. With Dendrite your can:

* Authenticate on websites
* Interact with elements
* Extract structured data
* Download and upload files
* Fill out forms

For example, if you want to create an AI agent that can log into your bank and analyze it's cashflow, it would be easy to create an `analyze_cashflow` action with Dendrite!


## Get your API keys

First, let's get an Dendrite API key from the [dashboard](https://dendrite.se/app).

You'll also need an [OpenAI](https://platform.openai.com/) and [Anthropic](https://console.anthropic.com/settings/keys) API key. We use their LLMs to complete certain task, so make sure you have valid API keys.

You can use the keys in your code or have them in a `.env` file like this:

```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
DENDRITE_API_KEY=
```


## Installation

Install the Dendrite SDK. We also need to run playwright install to install the browser drivers.


With pip:
```
pip install dendrite-sdk && playwright install 
```

With poetry:
```
poetry add dendrite-sdk && poetry run playwright install 
```


## Hello World Example

For our first Dendrite script, let's start the `DendriteBrowser`, go to google.com and enter "hello world" into the search field:

```python main.py
import asyncio
from dendrite_sdk import DendriteBrowser


async def hello_world():
    # You need to provide an Open AI key and an Anthropic key.
    openai_api_key = "..."
    anthropic_api_key = "..."

    # Get your Dendrite API get from Dendrite.se.
    dendrite_api_key = "..."

    # Initate the Dendrite Browser
    browser = DendriteBrowser(
        openai_api_key=openai_api_key,
        anthropic_api_key=anthropic_api_key,
        dendrite_api_key=dendrite_api_key,
    )

    # Navigate with `goto`, which returns a 'DendritePage' that controls the current page.
    page = await browser.goto("https://google.com")

    # Get elements from the current page with `get_element`.
    search_bar = await page.get_element("The search bar")
    
    # Let's enter hello world into the search bar.
    await search_bar.fill("hello world")


asyncio.run(hello_world())
```




[See more advanced examples in our docs.](https://docs.dendrite.se)

## Remote Browsers

When you want to scale up your AI agents, we support using browsers hosted by Browserbase. This way you can run many agents in parallel without having to worry about the infrastructure. 

To start using Browserbase just swap out the `DendriteBrowser` with `BrowserbaseBrowser` and add your Browserbase API key and project id, either in the code or in a `.env` file like this:

```bash
# ... previous keys 
BROWSERBASE_API_KEY=
BROWSERBASE_PROJECT_ID=
```



```python
# from dendrite_python_sdk import DendriteBrowser
from dendrite_sdk.ext.browserbase import BrowserbaseBrowser

... 

# browser = DendriteBrowser(...)
browser = BrowserbaseBrowser(
    # Include the previous arguments from DendriteBrowser
    browserbase_api_key="...", # or specify the browsebase keys in the .env file
    browserbase_project_id="..." 
)

...

```