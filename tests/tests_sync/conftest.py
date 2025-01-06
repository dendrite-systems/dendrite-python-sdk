import pytest

from dendrite import Dendrite


@pytest.fixture(scope="session")
def dendrite_browser():
    """
    Initializes a single instance of Dendrite to be shared across multiple test cases.

    The fixture has a session scope, so it will only be initialized once for the entire test session.
    """
    browser = Dendrite(
        playwright_options={"headless": True},
    )  # Launch the browser

    yield browser  # Provide the browser to tests

    # Cleanup after all tests are done
    browser.close()
