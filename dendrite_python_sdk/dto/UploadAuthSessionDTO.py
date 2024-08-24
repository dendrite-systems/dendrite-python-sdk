from pydantic import BaseModel

from dendrite_python_sdk.dendrite_browser.authentication.auth_session import (
    AuthSession,
    StorageState,
)


class UploadAuthSessionDTO(BaseModel):
    auth_data: AuthSession
    storage_state: StorageState
