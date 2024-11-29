from typing import Generic, TypeVar, TypedDict
from pydantic import BaseModel

from dendrite.logic.cache.file_cache import FileCache
from dendrite.models.scripts import Script
from dendrite.models.selector import Selector

element_cache = FileCache(Selector, "./cache/get_element.json")
