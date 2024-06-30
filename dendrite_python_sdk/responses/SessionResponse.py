from typing import List
from pydantic import BaseModel


class SessionResponse(BaseModel):
    session_data: List[dict]
    