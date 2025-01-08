from pathlib import Path
from typing import Optional, Union

from playwright.async_api import StorageState

from dendrite.logic.cache.file_cache import FileCache
from dendrite.logic.llm.config import LLMConfig
from dendrite.models.scripts import Script
from dendrite.models.selector import Selector


class Config:
    """
    Configuration class for Dendrite that manages file paths and LLM settings.

    This class handles the configuration of cache locations, authentication sessions,
    and LLM (Language Learning Model) settings for the Dendrite system.

    Attributes:
        cache_path (Path): Path to the cache directory
        llm_config (LLMConfig): Configuration for language learning models
        extract_cache (FileCache): Cache for extracted script data
        element_cache (FileCache): Cache for element selectors
        storage_cache (FileCache): Cache for browser storage states
        auth_session_path (Path): Path to authentication session data
    """

    def __init__(
        self,
        root_path: Union[str, Path] = ".dendrite",
        cache_path: Union[str, Path] = "cache",
        auth_session_path: Union[str, Path] = "auth",
        llm_config: Optional[LLMConfig] = None,
    ):
        """
        Initialize the Config with specified paths and LLM configuration.

        Args:
            root_path (Union[str, Path]): Base directory for all Dendrite data.
                Defaults to ".dendrite".
            cache_path (Union[str, Path]): Directory name for cache storage relative
                to root_path. Defaults to "cache".
            auth_session_path (Union[str, Path]): Directory name for authentication
                sessions relative to root_path. Defaults to "auth".
            llm_config (Optional[LLMConfig]): Configuration for language models.
                If None, creates a default LLMConfig instance.
        """
        self.cache_path = root_path / Path(cache_path)
        self.llm_config = llm_config or LLMConfig()
        self.extract_cache = FileCache(Script, self.cache_path / "extract.json")
        self.element_cache = FileCache(Selector, self.cache_path / "get_element.json")
        self.storage_cache = FileCache(
            StorageState, self.cache_path / "storage_state.json"
        )
        self.auth_session_path = root_path / Path(auth_session_path)
