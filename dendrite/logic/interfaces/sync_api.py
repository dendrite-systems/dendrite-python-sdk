import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading
from typing import Any, Coroutine, Protocol, TypeVar

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


class LogicAPIProtocol(Protocol):

    def get_element(self, dto: GetElementsDTO) -> GetElementResponse: ...

    def verify_action(self, dto: VerifyActionDTO) -> InteractionResponse: ...

    def extract(self, dto: ExtractDTO) -> ExtractResponse: ...

    def ask_page(self, dto: AskPageDTO) -> AskPageResponse: ...


class SyncProtocol(LogicAPIProtocol):
    def get_element(self, dto: GetElementsDTO) -> GetElementResponse:
        return run_coroutine_sync(get_element.get_element(dto))

    def extract(self, dto: ExtractDTO) -> ExtractResponse:
        return run_coroutine_sync(extract.extract(dto))

    def verify_action(self, dto: VerifyActionDTO) -> InteractionResponse:
        return run_coroutine_sync(verify_interaction.verify_action(dto))

    def ask_page(self, dto: AskPageDTO) -> AskPageResponse:
        return run_coroutine_sync(ask.ask_page_action(dto))
