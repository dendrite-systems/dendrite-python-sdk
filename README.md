> **Notice:** The Dendrite SDK is not under active development from us. However, the project will remain fully open source so that you and others can learn from and build upon our work. Feel free to fork, study, or adapt this code for your own projects as you wish – reach out to us on Discord if you have questions!

<p align="center">
  <a href="https://dendrite.systems"><img src="https://img.shields.io/badge/Website-dendrite.systems-blue?style=for-the-badge&logo=google-chrome" alt="Dendrite Homepage"></a>
  <a href="https://docs.dendrite.systems"><img src="https://img.shields.io/badge/Docs-docs.dendrite.systems-orange?style=for-the-badge&logo=bookstack" alt="Docs"></a>
  <a href="https://discord.gg/ETPBdXU3kx"><img src="https://img.shields.io/badge/Discord-Join%20Us-7289DA?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
</p>

## What is Dendrite?

#### Dendrite is a framework that makes it easy for web AI agents to browse the internet just like humans do. Use Dendrite to:

- 👆🏼 Interact with elements
- 💿 Extract structured data
- 🔓 Authenticate on websites
- ↕️ Download/upload files
- 🚫 Browse without getting blocked


#### A simple outlook integration

With Dendrite, it's easy to create web interaction tools for your agent.

```python
from dendrite import AsyncDendrite


async def send_email(to, subject, message):
    client = AsyncDendrite(auth="outlook.live.com")

    # Navigate
    await client.goto(
        "https://outlook.live.com/mail/0/", expected_page="An email inbox"
    )

    # Create new email and populate fields
    await client.click("The new email button")
    await client.fill("The recipient field", to)
    await client.press("Enter")
    await client.fill("The subject field", subject)
    await client.fill("The message field", message)

    # Send email
    await client.press("Enter", hold_cmd=True)


if __name__ == "__main__":
    import asyncio

    asyncio.run(send_email("test@example.com", "Hello", "This is a test email"))

```

To authenticate on outlook, run the command below:

```bash
dendrite auth --url outlook.live.com
```

A browser will open and you'll be able to login. After you've logged in, press enter in your terminal to save the cookies locally, so that they can be used in your code.

Read more about authentication [in our docs](https://docs.dendrite.systems/examples/authentication).

## Quickstart

```
pip install dendrite && dendrite install
```

#### Simple navigation and interaction

Initialize the Dendrite client and start doing web interactions without boilerplate.

[Get your API key here](https://dendrite.systems/app)

```python
from dendrite import AsyncDendrite

async def main():
    client = AsyncDendrite(dendrite_api_key="sk...")

    await client.goto("https://google.com")
    await client.fill("Search field", "Hello world")
    await client.press("Enter")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

In the example above, we simply go to Google, populate the search field with "Hello world" and simulate a keypress on Enter. It's a simple example that starts to explore the endless possibilities with Dendrite. Now you can create tools for your agents that have access to the full web without depending on APIs.

## More Examples

### Get any page as markdown

This is a simple example of how to get any page as markdown.

```python
from dendrite import AsyncDendrite
from dotenv import load_dotenv

async def main():
    browser = AsyncDendrite()

    await browser.goto("https://dendrite.systems")
    await browser.wait_for("the page to load")

    # Get the entire page as markdown
    md = await browser.markdown()
    print(md)
    print("=" * 200)

    # Only get a certain part of the page as markdown
    data_extraction_md = await browser.markdown("the part about data extraction")
    print(data_extraction_md)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Extract Data from Google Analytics

Here's how to get the amount of monthly visitors from Google Analytics using the `extract` function:

```python
async def get_visitor_count() -> int:
    client = AsyncDendrite(auth="analytics.google.com")

    await client.goto(
      "https://analytics.google.com/analytics/web",
      expected_page="Google Analytics dashboard"
    )

    # The Dendrite extract agent will create a web script that is cached
    # and reused. It will self-heal when the website updates
    visitor_count = await client.extract("The amount of visitors this month", int)
    return visitor_count
```

### Download Bank Transactions

Here's tool that allows our AI agent to download our bank's monthly transactions so that they can be analyzed and compiled into a report.

```python
from dendrite import AsyncDendrite

async def get_transactions() -> str:
    client = AsyncDendrite(auth="mercury.com")

    # Navigate and wait for loading
    await client.goto(
      "https://app.mercury.com/transactions",
      expected_page="Dashboard with transactions"
    )
    await client.wait_for("The transactions to finish loading")

    # Modify filters
    await client.click("The 'add filter' button")
    await client.click("The 'show transactions for' dropdown")
    await client.click("The 'this month' option")

    # Download file
    await client.click("The 'export filtered' button")
    transactions = await client.get_download()

    # Save file locally
    path = "files/transactions.xlsx"
    await transactions.save_as(path)

    return path

async def analyze_transactions(path: str):
    ... # Analyze the transactions with LLM of our choice
```


## Documentation

[Read the full docs here](https://docs.dendrite.systems)

[Find more advanced examples in our docs.](https://docs.dendrite.systems/examples)

## Remote Browsers

When you want to scale up your AI agents, we support using browsers hosted by Browserbase. This way you can run many agents in parallel without having to worry about the infrastructure.

To start using Browserbase just swap out the `AsyncDendrite` class with `AsyncDendriteRemoteBrowser` and add your Browserbase API key and project id, either in the code or in a `.env` file like this:

```bash
# ... previous keys
BROWSERBASE_API_KEY=
BROWSERBASE_PROJECT_ID=
```

```python
# from dendrite import AsyncDendrite
from dendrite import AsyncDendriteRemoteBrowser

async def main():
    # client = AsyncDendrite(...)
    client = AsyncDendriteRemoteBrowser(
        # Use interchangeably with the AsyncDendrite class
        browserbase_api_key="...", # or specify the browsebase keys in the .env file
        browserbase_project_id="..."
    )
    ...

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```
