[![Website](https://img.shields.io/badge/Website-dendrite.systems-blue?style=for-the-badge&logo=google-chrome)](https://dendrite.systems)
[![Documentation](https://img.shields.io/badge/Docs-docs.dendrite.systems-orange?style=for-the-badge&logo=bookstack)](https://docs.dendrite.systems)
[![Discord](https://img.shields.io/badge/Discord-Join%20Us-7289DA?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/ETPBdXU3kx)

## What is Dendrite?

#### Dendrite is a devtool that makes it easy for AI agents to:

- 🔓 Authenticate on websites
- 👆🏼 Interact with elements
- 💿 Extract structured data
- ↕️ Download/upload files
- 🚫 Browse without getting blocked

#### A simple outlook integration

With Dendrite, it's easy to create web interaction tools for your agent.

```python
from dendrite_sdk import Dendrite

def send_email():
    client = Dendrite(auth="outlook.live.com")

    # Navigate
    client.goto("https://outlook.live.com/mail/0/")
    client.wait_for("The dashboard to finish loading")

    # Create new email and populate fields
    client.click("The new email button")
    client.fill_fields({
        "Recipient": to,
        "Subject": subject,
        "Message": message
    })

    # Send email
    client.click("The send button")
```

To authenticate you'll need to use our Chrome Extension **Dendrite Vault**, you can download it [here](https://chromewebstore.google.com/detail/dendrite-vault/faflkoombjlhkgieldilpijjnblgabnn). Read more about authentication [in our docs](https://docs.dendrite.systems/examples/authentication-instagram).

## Quickstart

```
pip install dendrite-sdk && dendrite install
```

#### Simple navigation and interaction

Initialize the Dendrite client and start doing web interactions without boilerplate.

[Get your API key here](https://dendrite.systems/app)

```python
from dendrite_sdk import Dendrite

client = Dendrite(dendrite_api_key="sk...")

client.goto("https://google.com")
client.fill("Search field", "Hello world")
client.press("Enter")
```

In the example above, we simply go to Google, populate the search field with "Hello world" and simulate a keypress on Enter. It's a simple example that starts to explore the endless possibilities with Dendrite. Now you can create tools for your agents that have access to the full web without depending on APIs.

## More powerful examples

Now, let's have some fun. Earlier we showed you a simple send_email example. And sending emails is cool, but if that's all our agent can do it kind of sucks. So let's create two cooler examples.

### Download Bank Transactions

First up, a tool that allows our AI agent to download our bank's monthly transactions so that they can be analyzed and compiled into a report that can be sent to stakeholders with `send_email`.

```python
from dendrite_sdk import Dendrite

def get_transactions() -> str:
    client = Dendrite(auth="mercury.com")

    # Navigate and wait for loading
    client.goto(
      "https://app.mercury.com/transactions",
      expected_page="Dashboard with transactions"
    )
    client.wait_for("The transactions to finish loading")

    # Modify filters
    client.click("The 'add filter' button")
    client.click("The 'show transactions for' dropdown")
    client.click("The 'this month' option")

    # Download file
    client.click("The 'export filtered' button")
    transactions = client.get_download()

    # Save file locally
    path = "files/transactions.xlsx"
    transactions.save_as(path)

    return path

def analyze_transactions(path: str):
    ...
```

### Extract Google Analytics

Finally, it would be cool if we could add the amount of monthly visitors from Google Analytics to our report. We can do that by using the `extract` function:

```python
def get_visitor_count() -> int:
    client = Dendrite(auth="analytics.google.com")

    client.goto(
      "https://analytics.google.com/analytics/web",
      expected_page="Google Analytics dashboard"
    )
    client.wait_for("The analytics page to finish loading")

    # The Dendrite extract agent will create a web script that is cached
    # and reused. It will self-heal when the website updates
    visitor_count = client.extract("The amount of visitors this month", int)
    return visitor_count
```

## Documentation

[Read the full docs here](https://docs.dendrite.systems)

[Find more advanced examples in our docs.](https://docs.dendrite.systems/examples)

## Remote Browsers

When you want to scale up your AI agents, we support using browsers hosted by Browserbase. This way you can run many agents in parallel without having to worry about the infrastructure.

To start using Browserbase just swap out the `Dendrite` class with `DendriteRemoteBrowser` and add your Browserbase API key and project id, either in the code or in a `.env` file like this:

```bash
# ... previous keys
BROWSERBASE_API_KEY=
BROWSERBASE_PROJECT_ID=
```

```python
# from dendrite_sdk import Dendrite
from dendrite_sdk import DendriteRemoteBrowser

...

# client = Dendrite(...)
client = DendriteRemoteBrowser(
    # Use interchangeably with the Dendrite class
    browserbase_api_key="...", # or specify the browsebase keys in the .env file
    browserbase_project_id="..."
)

...
```
