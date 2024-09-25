[![Website](https://img.shields.io/badge/Website-dendrite.systems-blue?style=for-the-badge&logo=google-chrome)](https://dendrite.systems)
[![Documentation](https://img.shields.io/badge/Docs-docs.dendrite.systems-orange?style=for-the-badge&logo=bookstack)](https://docs.dendrite.systems)
[![Discord](https://img.shields.io/badge/Discord-Join%20Us-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/ETPBdXU3kx)

## What is Dendrite?

#### Dendrite is a devtool that makes it easy for AI agents to:

- 🔓  Authenticate on websites
- 👆🏼  Interact with elements
- 💿  Extract structured data
- ↕️  Download/upload files
- 🚫  Browse without getting blocked

### Sending Emails
With Dendrite, you can code a **email sending tool** like this:

```python
from dendrite import DendriteBrowser

# Provide this tool to an agent by using e.g crewAI, llamaIndex, langchain or your own framework
async def send_email(to: str, subject: str, body: str):
  async with DendriteBrowser() as dendrite:

    # Your agent will be able to access your outlook account now. You can mirror your browser's auth sessions to your agent with our Chrome Extension "Dendrite Vault".
    await dendrite.authenticate("outlook.live.com") 

    page = await dendrite.goto("https://outlook.live.com/mail/0/")
    await page.wait_for("The emails and dashboard to be loaded")

    # The functions below are will be cached. Agents are only used once to find the correct element
    # When a website updates and cache fails, the elements will just be found again by the same agents
    await page.click("the new mail button") 
    await page.fill("the 'to' input", value=to)
    await page.fill("the subject input", value=subject)
    await page.fill("the mail content input", value=body)
    await page.click("the send button")
```

To authenticate you'll need to use our Chrome Extension **Dendrite Vault**, you can download it [here](https://chromewebstore.google.com/detail/dendrite-vault/faflkoombjlhkgieldilpijjnblgabnn). Read more about authentication [in our docs](https://docs.dendrite.systems/examples/authentication-instagram).

### Download Bank Transactions  
Sending emails is cool, but if that's all our agent can do it kind of sucks. So, let's create a tool that allows our AI agent to download our bank's monthly transactions so that they can be analyzed and compiled into a report that can be sent stakeholders with `send_email`.

```python
async def get_and_analyze_transactions(prompt: str) -> str:
    async with DendriteBrowser() as dendrite:
        await dendrite.authenticate("mercury.com")
        page = await dendrite.goto("https://app.mercury.com/transactions", expected_outcome="We should arrive at the dashboard") # Raise an exception if we aren't logged in. 
        await page.wait_for("The transactions page to have loaded")
        await page.click("the add filter button")
        await page.click("the show transactions for dropdown")
        await page.click("the 'this month' option")
        await page.click("the 'export filtered' button")
        transactions = await page.get_download()
        path = await transactions.save_as("transactions.xlsx")
        report = await code_interpreter_write_report("transactions.xlsx", prompt) # Let's use code interpreter to analyze and write a report.
        if report:
            return report
```

### Extract Google Analytics
Finally, it would be cool if we could add the amount of monthly visitors from Google Analytics to our report. We can do that by using the `extract` function:

```python
async def get_visitor_stats() -> int:
    async with DendriteBrowser() as dendrite:
        await dendrite.authenticate("analytics.google.com")
        page = await dendrite.goto("https://analytics.google.com/analytics/web")
        await page.wait_for("The analytics page to have loaded")
        
        # `extract` will create a Beautiful Soup script that is cached and reused until the website updates.
        visitor_amount = await page.extract("Get the amount of visitors on my site this month", int) 
        return visitor_amount
```

## Documentation

[Read the full docs here](https://docs.dendrite.systems)

## Get your API keys

Before you can start using Dendrite yourself, let's get an Dendrite API key from the [dashboard](https://dendrite.systems/app).

You'll also need an [OpenAI](https://platform.openai.com/) and [Anthropic](https://console.anthropic.com/settings/keys) API key. We use their LLMs to complete certain tasks, so make sure you have valid API keys.

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

## More Examples

For more examples 

[See more advanced examples in our docs.](https://docs.dendrite.systems)

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
from dendrite_sdk.async_api.ext.browserbase import BrowserbaseBrowser

... 

# browser = DendriteBrowser(...)
browser = BrowserbaseBrowser(
    # Include the previous arguments from DendriteBrowser
    browserbase_api_key="...", # or specify the browsebase keys in the .env file
    browserbase_project_id="..." 
)

...

```
