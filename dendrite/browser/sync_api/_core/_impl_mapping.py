from typing import Dict, Optional, Type
from dendrite.browser.sync_api._core._impl_browser import ImplBrowser
from dendrite.browser.sync_api._core._local_browser_impl import LocalImpl
from dendrite.browser.sync_api._remote_impl.browserbase._impl import BrowserBaseImpl
from dendrite.browser.sync_api._remote_impl.browserless._impl import BrowserlessImpl
from dendrite.browser.remote import Providers
from dendrite.browser.remote.browserbase_config import BrowserbaseConfig
from dendrite.browser.remote.browserless_config import BrowserlessConfig

IMPL_MAPPING: Dict[Type[Providers], Type[ImplBrowser]] = {
    BrowserbaseConfig: BrowserBaseImpl,
    BrowserlessConfig: BrowserlessImpl,
}
SETTINGS_CLASSES: Dict[str, Type[Providers]] = {
    "browserbase": BrowserbaseConfig,
    "browserless": BrowserlessConfig,
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
