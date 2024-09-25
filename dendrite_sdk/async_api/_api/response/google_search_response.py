from typing import List
from pydantic import BaseModel


class SearchResult(BaseModel):
    url: str
    title: str
    description: str


class GoogleSearchResponse(BaseModel):
    results: List[SearchResult]
