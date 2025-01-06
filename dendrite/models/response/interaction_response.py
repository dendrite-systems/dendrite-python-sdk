from pydantic import BaseModel

from dendrite.models.status import Status


class InteractionResponse(BaseModel):
    message: str
    status: Status
