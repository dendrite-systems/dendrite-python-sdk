from typing import Union
from dendrite_sdk.remote.browserless_config import BrowserlessConfig
from dendrite_sdk.remote.browserbase_config import BrowserbaseConfig


Providers = Union[BrowserbaseConfig, BrowserlessConfig]

__all__ = ["Providers", "BrowserbaseConfig"]
