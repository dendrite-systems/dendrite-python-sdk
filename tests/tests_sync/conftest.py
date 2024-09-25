import pytest
from dendrite_sdk.sync_api import DendriteBrowser


@pytest.fixture(scope="session")
def dendrite_browser():
    """
    Initializes a single instance of DendriteBrowser to be shared across multiple test cases.

    The fixture has a session scope, so it will only be initialized once for the entire test session.
    """
    browser = DendriteBrowser(
        openai_api_key="your_openai_api_key",
        dendrite_api_key="your_dendrite_api_key",
        anthropic_api_key="your_anthropic_api_key",
    )  # Launch the browser

    yield browser  # Provide the browser to tests

    # Cleanup after all tests are done
    browser.close()
