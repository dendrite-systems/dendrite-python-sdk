from typing import Union
from dendrite.browser.remote.browserless_config import BrowserlessConfig
from dendrite.browser.remote.browserbase_config import BrowserbaseConfig


Providers = Union[BrowserbaseConfig, BrowserlessConfig]

__all__ = ["Providers", "BrowserbaseConfig"]
