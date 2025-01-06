from typing import Dict, Optional, Type

from dendrite.browser.remote import Providers
from dendrite.browser.remote.browserbase_config import BrowserbaseConfig
from dendrite.browser.remote.browserless_config import BrowserlessConfig

from ..protocol.browser_protocol import BrowserProtocol
from .browserbase._impl import BrowserbaseImpl
from .browserless._impl import BrowserlessImpl
from .local._impl import LocalImpl

IMPL_MAPPING: Dict[Type[Providers], Type[BrowserProtocol]] = {
    BrowserbaseConfig: BrowserbaseImpl,
    BrowserlessConfig: BrowserlessImpl,
}

SETTINGS_CLASSES: Dict[str, Type[Providers]] = {
    "browserbase": BrowserbaseConfig,
    "browserless": BrowserlessConfig,
}


def get_impl(remote_provider: Optional[Providers]) -> BrowserProtocol:
    if remote_provider is None:
        return LocalImpl()

    try:
        provider_class = IMPL_MAPPING[type(remote_provider)]
    except KeyError:
        raise ValueError(
            f"No implementation for {type(remote_provider)}. Available providers: {', '.join(map(lambda x: x.__name__, IMPL_MAPPING.keys()))}"
        )

    return provider_class(remote_provider)
