from typing import Literal
from pydantic import BaseModel

Status = Literal["success", "failed"]


class InteractionResponse(BaseModel):
    message: str
    status: Status
