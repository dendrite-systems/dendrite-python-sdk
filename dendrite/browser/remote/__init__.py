from typing import Union

from dendrite.browser.remote.browserbase_config import BrowserbaseConfig
from dendrite.browser.remote.browserless_config import BrowserlessConfig

Providers = Union[BrowserbaseConfig, BrowserlessConfig]

__all__ = ["Providers", "BrowserbaseConfig"]
