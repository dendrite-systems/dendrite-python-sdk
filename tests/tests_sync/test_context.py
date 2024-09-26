# content of test_tmp_path.py
import os
from dendrite_sdk.sync_api import Dendrite


def test_context_manager():
    with Dendrite() as browser:
        browser.goto("https://dendrite.systems")
