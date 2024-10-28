from pydantic import BaseModel


class SelectorCacheResponse(BaseModel):
    exists: bool
