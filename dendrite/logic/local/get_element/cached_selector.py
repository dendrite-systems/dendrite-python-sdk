from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from loguru import logger
from pydantic import BaseModel

from dendrite.logic.interfaces.cache import CacheProtocol


class Selector(BaseModel):
    selector: str
    prompt: str
    url: str
    netloc: str
    created_at: str


def deserialize_selector(selector_from_db) -> Selector:
    return Selector(
        selector=str(selector_from_db["selector"]),
        prompt=selector_from_db.get("prompts", ""),
        url=selector_from_db.get("url", ""),
        netloc=selector_from_db.get("netloc", ""),
        created_at=selector_from_db.get("created_at", ""),
    )


async def get_selector_from_db(
    url: str, prompt: str, cache: CacheProtocol[Selector] 
) -> Optional[Selector]:

    netloc = urlparse(url).netloc

    return cache.get({"netloc": netloc, "prompt": prompt})

async def add_selector_in_db(
    prompt: str, bs4_selector: str, url: str 
):

    created_at = datetime.now().isoformat()
    netloc = urlparse(url).netloc
    selector: Selector = Selector(
        prompt=prompt,
        selector=bs4_selector,
        url=url,
        netloc=netloc,
        created_at=created_at,
    )
    serialized = selector.model_dump()
        # res = await selector_collection.insert_one(serialized)
        # return str(res.inserted_id)




