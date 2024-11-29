from datetime import datetime
from typing import Optional, Type
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from loguru import logger
from pydantic import BaseModel


from dendrite.logic.cache.file_cache import FileCache
from dendrite.models.selector import Selector
from dendrite.logic.config import config


async def get_selector_from_cache(
    url: str, prompt: str, cache: FileCache[Selector]
) -> Optional[Selector]:
    netloc = urlparse(url).netloc

    return cache.get({"netloc": netloc, "prompt": prompt})


async def add_selector_to_cache(prompt: str, bs4_selector: str, url: str) -> None:
    cache = config.element_cache
    created_at = datetime.now().isoformat()
    netloc = urlparse(url).netloc
    selector: Selector = Selector(
        prompt=prompt,
        selector=bs4_selector,
        url=url,
        netloc=netloc,
        created_at=created_at,
    )

    cache.set({"netloc": netloc, "prompt": prompt}, selector)
