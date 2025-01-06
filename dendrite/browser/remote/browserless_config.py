import os
from typing import Optional

from dendrite.browser._common._exceptions.dendrite_exception import MissingApiKeyError


class BrowserlessConfig:
    def __init__(
        self,
        url: str = "wss://production-sfo.browserless.io",
        api_key: Optional[str] = None,
        proxy: Optional[str] = None,
        proxy_country: Optional[str] = None,
        block_ads: bool = False,
    ):
        api_key = api_key if api_key is not None else os.getenv("BROWSERLESS_API_KEY")
        if api_key is None:
            raise MissingApiKeyError("BROWSERLESS_API_KEY")

        self.url = url
        self.api_key = api_key
        self.block_ads = block_ads
        self.proxy = proxy
        self.proxy_country = proxy_country
