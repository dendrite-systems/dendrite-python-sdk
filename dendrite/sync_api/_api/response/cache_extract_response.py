from pydantic import BaseModel


class CacheExtractResponse(BaseModel):
    exists: bool
