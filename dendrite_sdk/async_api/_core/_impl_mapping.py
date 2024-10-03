from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

from dendrite_sdk.async_api._core._impl_browser import ImplBrowser, LocalImpl
from dendrite_sdk.async_api._core._type_spec import Providers
from dendrite_sdk.async_api.ext.browserbase._impl import BrowserBaseImpl
from dendrite_sdk.async_api.ext.browserbase._settings import BrowserBaseSettings
from dendrite_sdk.ext.bfloat_provider import BFloatProviderConfig
from dendrite_sdk.ext.browserbase_provider import BrowserbaseConfig


IMPL_MAPPING: Dict[Type[Providers], Type[ImplBrowser]] = {
    BrowserbaseConfig: BrowserBaseImpl,
    # BFloatProviderConfig: ,
}

SETTINGS_CLASSES: Dict[str, Type[BrowserbaseConfig]] = {
    "browserbase": BrowserbaseConfig,
}


def get_impl(remote_provider: Optional[Providers]) -> ImplBrowser:
    if remote_provider is None:
        return LocalImpl()

    try:
        provider_class = IMPL_MAPPING[type(remote_provider)]
    except KeyError:
        raise ValueError(
            f"No implementation for {type(remote_provider)}. Available providers: {', '.join(map(lambda x: x.__name__, IMPL_MAPPING.keys()))}"
        )

    return provider_class(remote_provider)
