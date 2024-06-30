from typing import List
from pydantic import BaseModel


class UploadSessionDTO(BaseModel):
    user_id: str
    domain: str
    session_data: List[dict]