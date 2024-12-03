from pathlib import Path
from typing import Optional, Union
from dendrite.logic.cache.file_cache import FileCache
from dendrite.logic.llm.config import LLMConfig
from dendrite.models.scripts import Script
from dendrite.models.selector import Selector


class Config:
    def __init__(
        self,
        cache_path: Optional[Union[str, Path]] = None,
        llm_config: Optional[LLMConfig] = None,
    ):
        self.cache_path = Path(cache_path) if cache_path else Path("./.dendrite/cache")
        self.llm_config = llm_config or LLMConfig()
        self.extract_cache = FileCache(Script, self.cache_path / "extract.json")
        self.element_cache = FileCache(Selector, self.cache_path / "get_element.json")
