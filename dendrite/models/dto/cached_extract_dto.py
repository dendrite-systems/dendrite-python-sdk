from pydantic import BaseModel


class CachedExtractDTO(BaseModel):
    url: str
    prompt: str
