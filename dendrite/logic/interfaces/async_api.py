# dendrite/browser/async_api/_api/protocols.py
from typing import Protocol, Optional
from dendrite.browser.async_api._api.dto.authenticate_dto import AuthenticateDTO
from dendrite.browser.async_api._api.dto.upload_auth_session_dto import UploadAuthSessionDTO
from dendrite.browser.async_api._api.dto.get_elements_dto import (
    GetElementsDTO,
    CheckSelectorCacheDTO,
)
from dendrite.browser.async_api._api.dto.make_interaction_dto import MakeInteractionDTO
from dendrite.browser.async_api._api.dto.extract_dto import ExtractDTO
from dendrite.browser.async_api._api.dto.ask_page_dto import AskPageDTO
from dendrite.browser.async_api._api.dto.try_run_script_dto import TryRunScriptDTO
from dendrite.browser.async_api._api.response.selector_cache_response import SelectorCacheResponse
from dendrite.browser.async_api._api.response.get_element_response import GetElementResponse
from dendrite.browser.async_api._api.response.interaction_response import InteractionResponse
from dendrite.browser.async_api._api.response.extract_response import ExtractResponse
from dendrite.browser.async_api._api.response.ask_page_response import AskPageResponse
from dendrite.browser.async_api._api.response.cache_extract_response import CacheExtractResponse
from dendrite.browser.async_api._core.models.authentication import AuthSession


class BrowserAPIProtocol(Protocol):
    async def authenticate(self, dto: AuthenticateDTO) -> AuthSession:
        ...

    async def upload_auth_session(self, dto: UploadAuthSessionDTO) -> None:
        ...

    async def check_selector_cache(self, dto: CheckSelectorCacheDTO) -> SelectorCacheResponse:
        ...

    async def get_interactions_selector(self, dto: GetElementsDTO) -> GetElementResponse:
        ...

    async def make_interaction(self, dto: MakeInteractionDTO) -> InteractionResponse:
        ...

    async def check_extract_cache(self, dto: ExtractDTO) -> CacheExtractResponse:
        ...

    async def extract(self, dto: ExtractDTO) -> ExtractResponse:
        ...

    async def ask_page(self, dto: AskPageDTO) -> AskPageResponse:
        ...

    async def try_run_cached(self, dto: TryRunScriptDTO) -> Optional[ExtractResponse]:
        ...