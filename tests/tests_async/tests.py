import pytest
from dendrite_sdk import AsyncDendrite


@pytest.mark.asyncio
async def test_get_element():
    """Test the get_element method retrieves an existing element."""
    browser = AsyncDendrite()
    try:
        page = await browser.goto("https://example.com")
        element = await page.get_element("The main heading")
        assert element is not None
        assert await element.locator.inner_text() == "Example Domain"
    finally:
        await browser.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "link_text, expected_url",
    [
        ("the more information link", "https://www.iana.org/help/example-domains"),
    ],
)
async def test_click(link_text, expected_url):
    """Test the click method navigates to the correct URL."""
    browser = AsyncDendrite()
    try:
        page = await browser.goto("https://example.com")
        await page.click(link_text)
        assert expected_url in page.url
    finally:
        await browser.close()


@pytest.mark.asyncio
async def test_fill():
    """Test the fill method correctly inputs text into a form field."""
    browser = AsyncDendrite()
    try:
        page = await browser.goto("https://www.scrapethissite.com/pages/forms/")
        test_input = "Dendrite test"
        await page.fill("The search for teams input", test_input)
        search_input = await page.get_element("The search for teams input")
        assert search_input is not None
        assert await search_input.locator.input_value() == test_input
    finally:
        await browser.close()


@pytest.mark.asyncio
async def test_extract():
    """Test the extract method retrieves the correct page title."""
    browser = AsyncDendrite()
    try:
        page = await browser.goto("https://example.com")
        title = await page.extract("Get the page title", str)
        assert title == "Example Domain"
    finally:
        await browser.close()


@pytest.mark.asyncio
async def test_wait_for():
    """Test the wait_for method waits for a specific condition."""
    browser = AsyncDendrite()
    try:
        page = await browser.goto("https://example.com")
        await page.wait_for("The page to fully load and the main heading to be visible")
        main_heading = await page.get_element("The main heading")
        assert main_heading is not None
        assert await main_heading.locator.is_visible()
    finally:
        await browser.close()


@pytest.mark.asyncio
async def test_ask():
    """Test the ask method returns a relevant response."""
    browser = AsyncDendrite()
    try:
        page = await browser.goto("https://example.com")
        response = await page.ask("What is the main topic of this page?", str)
        assert "example" in response.lower()
        assert "domain" in response.lower()
    finally:
        await browser.close()
