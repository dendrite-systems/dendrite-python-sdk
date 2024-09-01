from pydantic import BaseModel

from dendrite_sdk._core.models.authentication import (
    AuthSession,
    StorageState,
)


class UploadAuthSessionDTO(BaseModel):
    auth_data: AuthSession
    storage_state: StorageState
