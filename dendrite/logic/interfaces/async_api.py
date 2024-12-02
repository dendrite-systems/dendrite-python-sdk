from typing import Protocol

from dendrite.browser.async_api._core.models.authentication import AuthSession
from dendrite.logic.get_element import get_element
from dendrite.models.dto.ask_page_dto import AskPageDTO
from dendrite.models.dto.extract_dto import ExtractDTO
from dendrite.models.dto.get_elements_dto import CheckSelectorCacheDTO, GetElementsDTO
from dendrite.models.dto.make_interaction_dto import VerifyActionDTO
from dendrite.models.response.ask_page_response import AskPageResponse

from dendrite.models.response.extract_response import ExtractResponse
from dendrite.models.response.get_element_response import GetElementResponse
from dendrite.models.response.interaction_response import InteractionResponse

from dendrite.logic.ask import ask
from dendrite.logic.extract import extract
from dendrite.logic import verify_interaction


class LogicAPIProtocol(Protocol):

    async def get_element(self, dto: GetElementsDTO) -> GetElementResponse: ...

    async def verify_action(self, dto: VerifyActionDTO) -> InteractionResponse: ...

    async def extract(self, dto: ExtractDTO) -> ExtractResponse: ...

    async def ask_page(self, dto: AskPageDTO) -> AskPageResponse: ...


class AsyncProtocol(LogicAPIProtocol):
    async def get_element(self, dto: GetElementsDTO) -> GetElementResponse:
        return await get_element.get_element(dto)

    # async def get_cached_selectors(self, dto: CheckSelectorCacheDTO) -> GetElementResponse:
    #     return await get_element.get_cached_selectors(dto)

    async def extract(self, dto: ExtractDTO) -> ExtractResponse:
        return await extract.extract(dto)

    async def verify_action(self, dto: VerifyActionDTO) -> InteractionResponse:
        return await verify_interaction.verify_action(dto)

    async def ask_page(self, dto: AskPageDTO) -> AskPageResponse:
        return await ask.ask_page_action(dto)
