from pydantic import BaseModel


class CachedSelectorDTO(BaseModel):
    url: str
    prompt: str
