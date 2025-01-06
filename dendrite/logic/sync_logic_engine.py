import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Coroutine, List, TypeVar

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

T = TypeVar("T")


def run_coroutine_sync(coroutine: Coroutine[Any, Any, T], timeout: float = 30) -> T:
    def run_in_new_loop():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coroutine)
        finally:
            new_loop.close()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    if threading.current_thread() is threading.main_thread():
        if not loop.is_running():
            return loop.run_until_complete(coroutine)
        else:
            with ThreadPoolExecutor() as pool:
                future = pool.submit(run_in_new_loop)
                return future.result(timeout=timeout)
    else:
        return asyncio.run_coroutine_threadsafe(coroutine, loop).result()


class LogicEngine:

    def __init__(self, config: Config):
        self._config = config

    def get_element(self, dto: GetElementsDTO) -> GetElementResponse:
        return run_coroutine_sync(get_element.get_element(dto, self._config))

    def get_cached_selectors(self, dto: CachedSelectorDTO) -> List[Selector]:
        return run_coroutine_sync(get_element.get_cached_selector(dto, self._config))

    def get_cached_scripts(self, dto: CachedExtractDTO) -> List[Script]:
        return run_coroutine_sync(extract.get_cached_scripts(dto, self._config))

    def extract(self, dto: ExtractDTO) -> ExtractResponse:
        return run_coroutine_sync(extract.extract(dto, self._config))

    def verify_action(self, dto: VerifyActionDTO) -> InteractionResponse:
        return run_coroutine_sync(verify_interaction.verify_action(dto, self._config))

    def ask_page(self, dto: AskPageDTO) -> AskPageResponse:
        return run_coroutine_sync(ask.ask_page_action(dto, self._config))
