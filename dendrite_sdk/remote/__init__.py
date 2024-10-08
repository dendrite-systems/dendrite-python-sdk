from typing import Union
from dendrite_sdk.async_api._ext_impl.browserless._settings import BrowserlessConfig
from dendrite_sdk.remote.browserbase_config import BrowserbaseConfig


Providers = Union[BrowserbaseConfig, BrowserlessConfig]

__all__ = ["Providers", "BrowserbaseConfig"]
