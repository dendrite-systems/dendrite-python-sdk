from typing import Optional
from loguru import logger
from dendrite.sync_api._api.response.cache_extract_response import CacheExtractResponse
from dendrite.sync_api._api.response.selector_cache_response import (
    SelectorCacheResponse,
)
from dendrite.sync_api._core.models.authentication import AuthSession
from dendrite.sync_api._api.response.get_element_response import GetElementResponse
from dendrite.sync_api._api.dto.ask_page_dto import AskPageDTO
from dendrite.sync_api._api.dto.authenticate_dto import AuthenticateDTO
from dendrite.sync_api._api.dto.get_elements_dto import GetElementsDTO
from dendrite.sync_api._api.dto.make_interaction_dto import MakeInteractionDTO
from dendrite.sync_api._api.dto.extract_dto import ExtractDTO
from dendrite.sync_api._api.dto.try_run_script_dto import TryRunScriptDTO
from dendrite.sync_api._api.dto.upload_auth_session_dto import UploadAuthSessionDTO
from dendrite.sync_api._api.response.ask_page_response import AskPageResponse
from dendrite.sync_api._api.response.interaction_response import InteractionResponse
from dendrite.sync_api._api.response.extract_response import ExtractResponse
from dendrite.sync_api._api._http_client import HTTPClient
from dendrite._common._exceptions.dendrite_exception import InvalidAuthSessionError
from dendrite.sync_api._api.dto.get_elements_dto import CheckSelectorCacheDTO


class BrowserAPIClient(HTTPClient):

    def authenticate(self, dto: AuthenticateDTO):
        res = self.send_request(
            "actions/authenticate", data=dto.model_dump(), method="POST"
        )
        if res.status_code == 204:
            raise InvalidAuthSessionError(domain=dto.domains)
        return AuthSession(**res.json())

    def upload_auth_session(self, dto: UploadAuthSessionDTO):
        self.send_request("actions/upload-auth-session", data=dto.dict(), method="POST")

    def check_selector_cache(self, dto: CheckSelectorCacheDTO) -> SelectorCacheResponse:
        res = self.send_request(
            "actions/check-selector-cache", data=dto.dict(), method="POST"
        )
        return SelectorCacheResponse(**res.json())

    def get_interactions_selector(self, dto: GetElementsDTO) -> GetElementResponse:
        res = self.send_request(
            "actions/get-interaction-selector", data=dto.dict(), method="POST"
        )
        return GetElementResponse(**res.json())

    def make_interaction(self, dto: MakeInteractionDTO) -> InteractionResponse:
        res = self.send_request(
            "actions/make-interaction", data=dto.dict(), method="POST"
        )
        res_dict = res.json()
        return InteractionResponse(
            status=res_dict["status"], message=res_dict["message"]
        )

    def check_extract_cache(self, dto: ExtractDTO) -> CacheExtractResponse:
        res = self.send_request(
            "actions/check-extract-cache", data=dto.dict(), method="POST"
        )
        return CacheExtractResponse(**res.json())

    def extract(self, dto: ExtractDTO) -> ExtractResponse:
        res = self.send_request("actions/extract-page", data=dto.dict(), method="POST")
        res_dict = res.json()
        return ExtractResponse(
            status=res_dict["status"],
            message=res_dict["message"],
            return_data=res_dict["return_data"],
            created_script=res_dict.get("created_script", None),
            used_cache=res_dict.get("used_cache", False),
        )

    def ask_page(self, dto: AskPageDTO) -> AskPageResponse:
        res = self.send_request("actions/ask-page", data=dto.dict(), method="POST")
        res_dict = res.json()
        return AskPageResponse(
            status=res_dict["status"],
            description=res_dict["description"],
            return_data=res_dict["return_data"],
        )

    def try_run_cached(self, dto: TryRunScriptDTO) -> Optional[ExtractResponse]:
        res = self.send_request(
            "actions/try-run-cached", data=dto.dict(), method="POST"
        )
        if res is None:
            return None
        res_dict = res.json()
        loaded_value = res_dict["return_data"]
        if loaded_value is None:
            return None
        return ExtractResponse(
            status=res_dict["status"],
            message=res_dict["message"],
            return_data=loaded_value,
            created_script=res_dict.get("created_script", None),
            used_cache=res_dict.get("used_cache", False),
        )
