from typing import Optional
from pydantic import BaseModel


class CompleteTaskDTO(BaseModel):
    message: str
    chat_id: Optional[str] = None
    stream: Optional[bool] = False
    store_chat: Optional[bool] = True
