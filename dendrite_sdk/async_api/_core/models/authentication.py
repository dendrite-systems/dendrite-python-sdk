from pydantic import BaseModel
from playwright.async_api import StorageState
from typing import List, Literal, Optional
from typing_extensions import TypedDict


class Cookie(TypedDict, total=False):
    name: str
    value: str
    domain: str
    path: str
    expires: float
    httpOnly: bool
    secure: bool
    sameSite: Literal["Lax", "None", "Strict"]


class LocalStorageEntry(TypedDict):
    name: str
    value: str


class OriginState(TypedDict):
    origin: str
    localStorage: List[LocalStorageEntry]


class StorageState(TypedDict, total=False):
    cookies: List[Cookie]
    origins: List[OriginState]


class DomainState(BaseModel):
    domain: str
    storage_state: StorageState


class AuthSession(BaseModel):
    user_agent: Optional[str]
    domain_states: List[DomainState]

    def to_storage_state(self) -> StorageState:
        cookies = []
        origins = []
        for domain_state in self.domain_states:
            cookies.extend(domain_state.storage_state.get("cookies", []))
            origins.extend(domain_state.storage_state.get("origins", []))
        return StorageState(cookies=cookies, origins=origins)
