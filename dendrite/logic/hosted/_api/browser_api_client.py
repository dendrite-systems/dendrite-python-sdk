from dendrite.browser.async_api._core.models.authentication import AuthSession
from dendrite.logic.hosted._api._http_client import HTTPClient
from dendrite.models.dto.ask_page_dto import AskPageDTO
from dendrite.models.dto.extract_dto import ExtractDTO
from dendrite.models.dto.get_elements_dto import GetElementsDTO
from dendrite.models.dto.make_interaction_dto import VerifyActionDTO
from dendrite.models.response.ask_page_response import AskPageResponse
from dendrite.models.response.extract_response import ExtractResponse
from dendrite.models.response.get_element_response import GetElementResponse
from dendrite.models.response.interaction_response import InteractionResponse


class BrowserAPIClient(HTTPClient):

    async def get_element(
        self, dto: GetElementsDTO
    ) -> GetElementResponse:
        res = await self.send_request(
            "actions/get-interaction-selector", data=dto.model_dump(), method="POST"
        )
        return GetElementResponse(**res.json())

    async def verify_action(self, dto: VerifyActionDTO) -> InteractionResponse:
        res = await self.send_request(
            "actions/make-interaction", data=dto.model_dump(), method="POST"
        )
        res_dict = res.json()
        return InteractionResponse(
            status=res_dict["status"], message=res_dict["message"]
        )

    async def extract(self, dto: ExtractDTO) -> ExtractResponse:
        res = await self.send_request(
            "actions/extract-page", data=dto.model_dump(), method="POST"
        )
        res_dict = res.json()
        return ExtractResponse(
            status=res_dict["status"],
            message=res_dict["message"],
            return_data=res_dict["return_data"],
            created_script=res_dict.get("created_script", None),
            used_cache=res_dict.get("used_cache", False),
        )

    async def ask_page(self, dto: AskPageDTO) -> AskPageResponse:
        res = await self.send_request(
            "actions/ask-page", data=dto.model_dump(), method="POST"
        )
        res_dict = res.json()
        return AskPageResponse(
            status=res_dict["status"],
            description=res_dict["description"],
            return_data=res_dict["return_data"],
        )
