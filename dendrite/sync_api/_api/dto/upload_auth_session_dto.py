from pydantic import BaseModel
from dendrite.sync_api._core.models.authentication import AuthSession, StorageState


class UploadAuthSessionDTO(BaseModel):
    auth_data: AuthSession
    storage_state: StorageState
