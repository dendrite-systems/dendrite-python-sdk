import pytest
import pytest_asyncio

from dendrite import AsyncDendrite
from dendrite.remote import BrowserbaseConfig  # Import your class here


@pytest_asyncio.fixture(scope="session")
async def dendrite_browser():
    """
    Initializes a single instance of AsyncDendrite to be shared across multiple test cases.

    The fixture has a session scope, so it will only be initialized once for the entire test session.
    """
    async with AsyncDendrite(
        playwright_options={"headless": True},
    ) as browser:
        yield browser  # Provide the browser to tests


@pytest_asyncio.fixture(scope="session")
async def browserbase():
    """
    Initializes a single instance of AsyncDendrite to be shared across multiple test cases.

    The fixture has a session scope, so it will only be initialized once for the entire test session.
    """
    async with AsyncDendrite(
        playwright_options={"headless": True},
        remote_config=BrowserbaseConfig(),
    ) as browser:
        yield browser  # Provide the browser to tests
