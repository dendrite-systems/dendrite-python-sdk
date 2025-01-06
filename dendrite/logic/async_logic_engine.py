from typing import List, Optional, Protocol

from dendrite.logic.ask import ask
from dendrite.logic.config import Config
from dendrite.logic.extract import extract
from dendrite.logic.get_element import get_element
from dendrite.logic.verify_interaction import verify_interaction
from dendrite.models.dto.ask_page_dto import AskPageDTO
from dendrite.models.dto.cached_extract_dto import CachedExtractDTO
from dendrite.models.dto.cached_selector_dto import CachedSelectorDTO
from dendrite.models.dto.extract_dto import ExtractDTO
from dendrite.models.dto.get_elements_dto import GetElementsDTO
from dendrite.models.dto.make_interaction_dto import VerifyActionDTO
from dendrite.models.response.ask_page_response import AskPageResponse
from dendrite.models.response.extract_response import ExtractResponse
from dendrite.models.response.get_element_response import GetElementResponse
from dendrite.models.response.interaction_response import InteractionResponse
from dendrite.models.scripts import Script
from dendrite.models.selector import Selector


class AsyncLogicEngine:
    def __init__(self, config: Config):
        self._config = config

    async def get_element(self, dto: GetElementsDTO) -> GetElementResponse:
        return await get_element.get_element(dto, self._config)

    async def get_cached_selectors(self, dto: CachedSelectorDTO) -> List[Selector]:
        return await get_element.get_cached_selector(dto, self._config)

    async def get_cached_scripts(self, dto: CachedExtractDTO) -> List[Script]:
        return await extract.get_cached_scripts(dto, self._config)

    async def extract(self, dto: ExtractDTO) -> ExtractResponse:
        return await extract.extract(dto, self._config)

    async def verify_action(self, dto: VerifyActionDTO) -> InteractionResponse:
        return await verify_interaction.verify_action(dto, self._config)

    async def ask_page(self, dto: AskPageDTO) -> AskPageResponse:
        return await ask.ask_page_action(dto, self._config)
