from pathlib import Path
from dendrite.logic.cache.file_cache import FileCache
from dendrite.models.scripts import Script
from dendrite.models.selector import Selector


class Config:
    def __init__(self):
        self.cache_path = Path("./cache") 
        self.llm_config = "8udjsad"
        self.extract_cache = FileCache(Script, self.cache_path / "extract.json")
        self.element_cache = FileCache(Selector, self.cache_path / "get_element.json")


config = Config()