from typing import List
from pydantic import BaseModel


class GetSessionDTO(BaseModel):
    user_id: str
    domain: str
