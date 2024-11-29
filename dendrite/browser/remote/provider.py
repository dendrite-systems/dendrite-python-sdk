from pathlib import Path
from typing import Union

from dendrite.browser.remote import Providers
from dendrite.browser.remote.browserbase_config import BrowserbaseConfig

try:
    import tomllib  # type: ignore
except ModuleNotFoundError:
    import tomli as tomllib  # tomllib is only included standard lib for python 3.11+


NAME_TO_CONFIG = {"browserbase": BrowserbaseConfig}


class ProviderConfig:
    @classmethod
    def from_toml(cls, path: Union[str, Path]) -> Providers:
        if isinstance(path, str):
            path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found at {path}")

        # Load the TOML config file

        config = tomllib.loads(path.read_text())

        remote_provider = config.get("remote_provider")
        if remote_provider is None:
            raise ValueError("Config file must contain a 'remote_provider' key")
        # Determine the provider type
        provider_type = remote_provider.get("name")
        if provider_type is None:
            raise ValueError("Config file must contain a 'remote_provider.name' key")

        # Get the corresponding config class
        config_class = NAME_TO_CONFIG.get(provider_type)
        if config_class is None:
            raise ValueError(
                f"Unsupported provider type: {provider_type}, must be one of {NAME_TO_CONFIG.keys()}"
            )

        settings = remote_provider.get("settings")
        if settings is None:
            raise ValueError(
                "Config file must contain a 'remote_provider.settings' key"
            )

        return config_class(**settings)
