from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from dendrite.logic.cache.file_cache import FileCache
from dendrite.models.selector import Selector


async def get_selector_from_cache(
    url: str, prompt: str, cache: FileCache[Selector]
) -> Optional[List[Selector]]:
    netloc = urlparse(url).netloc

    return cache.get({"netloc": netloc, "prompt": prompt})


async def add_selector_to_cache(
    prompt: str, bs4_selector: str, url: str, cache: FileCache[Selector]
) -> None:
    created_at = datetime.now().isoformat()
    netloc = urlparse(url).netloc
    selector: Selector = Selector(
        prompt=prompt,
        selector=bs4_selector,
        url=url,
        netloc=netloc,
        created_at=created_at,
    )

    cache.append({"netloc": netloc, "prompt": prompt}, selector)
