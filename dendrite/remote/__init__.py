from typing import Union
from dendrite.remote.browserless_config import BrowserlessConfig
from dendrite.remote.browserbase_config import BrowserbaseConfig


Providers = Union[BrowserbaseConfig, BrowserlessConfig]

__all__ = ["Providers", "BrowserbaseConfig"]
