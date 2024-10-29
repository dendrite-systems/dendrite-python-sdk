from pydantic import BaseModel
from dendrite.sync_api._common.status import Status


class InteractionResponse(BaseModel):
    message: str
    status: Status
