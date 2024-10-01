from typing import Optional
from loguru import logger
from dendrite_sdk.sync_api._core.models.authentication import AuthSession
from dendrite_sdk.sync_api._api.response.get_element_response import GetElementResponse
from dendrite_sdk.sync_api._api.dto.ask_page_dto import AskPageDTO
from dendrite_sdk.sync_api._api.dto.authenticate_dto import AuthenticateDTO
from dendrite_sdk.sync_api._api.dto.get_elements_dto import GetElementsDTO
from dendrite_sdk.sync_api._api.dto.make_interaction_dto import MakeInteractionDTO
from dendrite_sdk.sync_api._api.dto.scrape_page_dto import ScrapePageDTO
from dendrite_sdk.sync_api._api.dto.try_run_script_dto import TryRunScriptDTO
from dendrite_sdk.sync_api._api.dto.upload_auth_session_dto import UploadAuthSessionDTO
from dendrite_sdk.sync_api._api.response.ask_page_response import AskPageResponse
from dendrite_sdk.sync_api._api.response.interaction_response import InteractionResponse
from dendrite_sdk.sync_api._api.response.scrape_page_response import ScrapePageResponse
from dendrite_sdk.sync_api._api._http_client import HTTPClient
from dendrite_sdk._common._exceptions.dendrite_exception import InvalidAuthSessionError


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

    def scrape_page(self, dto: ScrapePageDTO) -> ScrapePageResponse:
        res = self.send_request("actions/extract-page", data=dto.dict(), method="POST")
        res_dict = res.json()
        return ScrapePageResponse(
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

    def try_run_cached(self, dto: TryRunScriptDTO) -> Optional[ScrapePageResponse]:
        res = self.send_request(
            "actions/try-run-cached", data=dto.dict(), method="POST"
        )
        if res is None:
            return None
        res_dict = res.json()
        loaded_value = res_dict["return_data"]
        if loaded_value is None:
            return None
        return ScrapePageResponse(
            status=res_dict["status"],
            message=res_dict["message"],
            return_data=loaded_value,
            created_script=res_dict.get("created_script", None),
            used_cache=res_dict.get("used_cache", False),
        )
