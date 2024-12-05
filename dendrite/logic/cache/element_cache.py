from typing import Generic, TypedDict, TypeVar

from pydantic import BaseModel

from dendrite.logic.cache.file_cache import FileCache
from dendrite.models.scripts import Script
from dendrite.models.selector import Selector

element_cache = FileCache(Selector, "./cache/get_element.json")
