from typing import Any, Dict, Optional, Type
from pydantic import BaseModel

from dendrite_sdk.async_api._core._impl_browser import BrowserBaseImpl, ImplBrowser


class BrowserBaseSettings(BaseModel):
    api_key: str
    project_id: str
    enable_proxy: bool = False
    enable_stealth: bool = True


class BFloatSettings(BaseModel):
    api_key: str
    enable_proxy: bool = True


class BFloatProvider(ImplBrowser):
    def __init__(self, settings: BFloatSettings):
        pass
        # Additional initialization

    def connect(self):
        # Implementation for BFloat
        pass


PROVIDER_CLASSES: Dict[str, Type[ImplBrowser]] = {
    "browserbase": BrowserBaseImpl,
    "bfloat": BFloatProvider,
}

SETTINGS_CLASSES: Dict[str, Type[BaseModel]] = {
    "browserbase": BrowserBaseSettings,
    "bfloat": BFloatSettings,
}


def get_impl(remote_provider: Optional[Dict[str, Any]]) -> ImplBrowser:
    if remote_provider is None:
        raise ValueError("Remote provider not specified")

    name = remote_provider.get("name")
    if name is None:
        raise ValueError("Remote provider name not specified")
    settings = remote_provider.get("settings")
    if settings is None:
        raise ValueError("Remote provider settings not specified")

    try:
        settings_class = SETTINGS_CLASSES[name.lower()]
        provider_class = PROVIDER_CLASSES[name.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown provider: {name}. Available providers: {', '.join(PROVIDER_CLASSES.keys())}"
        )
    settings = settings_class(**settings)
    return provider_class(settings)
