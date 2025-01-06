from pathlib import Path
from typing import Optional, Union

from playwright.async_api import StorageState

from dendrite.logic.cache.file_cache import FileCache
from dendrite.logic.llm.config import LLMConfig
from dendrite.models.scripts import Script
from dendrite.models.selector import Selector


class Config:
    def __init__(
        self,
        root_path: Union[str, Path] = ".dendrite",
        cache_path: Union[str, Path] = "cache",
        auth_session_path: Union[str, Path] = "auth",
        llm_config: Optional[LLMConfig] = None,
    ):
        self.cache_path = root_path / Path(cache_path)
        self.llm_config = llm_config or LLMConfig()
        self.extract_cache = FileCache(Script, self.cache_path / "extract.json")
        self.element_cache = FileCache(Selector, self.cache_path / "get_element.json")
        self.storage_cache = FileCache(
            StorageState, self.cache_path / "storage_state.json"
        )
        self.auth_session_path = root_path / Path(auth_session_path)
