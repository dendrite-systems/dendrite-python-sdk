# content of test_tmp_path.py
from dendrite import Dendrite


def test_context_manager():
    with Dendrite(
        playwright_options={"headless": True},
    ) as browser:
        browser.goto("https://dendrite.systems")
