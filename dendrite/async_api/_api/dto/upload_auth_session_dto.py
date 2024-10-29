from pydantic import BaseModel

from dendrite.async_api._core.models.authentication import (
    AuthSession,
    StorageState,
)


class UploadAuthSessionDTO(BaseModel):
    auth_data: AuthSession
    storage_state: StorageState
