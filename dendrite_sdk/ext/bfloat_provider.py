import os
from typing import Optional
from dendrite_sdk.exceptions import MissingApiKeyError


class BFloatProviderConfig:
    def __init__(
        self,
        api_key: Optional[str] = None,
        enable_proxy: bool = False,
    ):
        api_key = api_key if api_key is not None else os.getenv("BFLOAT_API_KEY")
        if api_key is None:
            raise MissingApiKeyError("BFLOAT_API_KEY")

        self.api_key = api_key
        self.enable_proxy = enable_proxy
