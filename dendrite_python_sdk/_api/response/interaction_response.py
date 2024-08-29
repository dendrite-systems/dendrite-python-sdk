from pydantic import BaseModel
from dendrite_python_sdk._common.status import Status


class InteractionResponse(BaseModel):
    message: str
    status: Status
