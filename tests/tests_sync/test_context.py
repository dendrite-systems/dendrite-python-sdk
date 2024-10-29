# content of test_tmp_path.py
import os
from dendrite.sync_api import Dendrite


def test_context_manager():
    with Dendrite(
        openai_api_key="your_openai_api_key",
        dendrite_api_key="your_dendrite_api_key",
        anthropic_api_key="your_anthropic_api_key",
        playwright_options={"headless": True},
    ) as browser:
        browser.goto("https://dendrite.systems")
