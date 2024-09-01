from typing import List
from pydantic import BaseModel


class SessionResponse(BaseModel):
    cookies: List[dict]
    origins_storage: List[dict]
