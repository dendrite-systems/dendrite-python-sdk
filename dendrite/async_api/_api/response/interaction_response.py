from pydantic import BaseModel
from dendrite.async_api._common.status import Status


class InteractionResponse(BaseModel):
    message: str
    status: Status
