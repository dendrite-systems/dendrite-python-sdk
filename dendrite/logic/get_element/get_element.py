from typing import List, Optional

from bs4 import BeautifulSoup, Tag
from loguru import logger

from dendrite.logic.config import Config
from dendrite.logic.dom.css import check_if_selector_successful, find_css_selector
from dendrite.logic.dom.strip import remove_hidden_elements
from dendrite.logic.get_element.cache import (
    add_selector_to_cache,
    get_selector_from_cache,
)
from dendrite.models.dto.cached_selector_dto import CachedSelectorDTO
from dendrite.models.dto.get_elements_dto import GetElementsDTO
from dendrite.models.response.get_element_response import GetElementResponse
from dendrite.models.selector import Selector

from .hanifi_search import hanifi_search


async def get_element(dto: GetElementsDTO, config: Config) -> GetElementResponse:
    if isinstance(dto.prompt, str):
        return await process_prompt(dto.prompt, dto, config)
    raise NotImplementedError("Prompt is not a string")


async def process_prompt(
    prompt: str, dto: GetElementsDTO, config: Config
) -> GetElementResponse:
    soup = BeautifulSoup(dto.page_information.raw_html, "lxml")
    return await get_new_element(soup, prompt, dto, config)


async def get_new_element(
    soup: BeautifulSoup, prompt: str, dto: GetElementsDTO, config: Config
) -> GetElementResponse:
    soup_without_hidden_elements = remove_hidden_elements(soup)
    element = await hanifi_search(
        soup_without_hidden_elements,
        prompt,
        config,
        dto.page_information.time_since_frame_navigated,
    )
    interactable = element[0]

    if interactable.status == "success":
        if interactable.dendrite_id is None:
            interactable.status = "failed"
            interactable.reason = "No d-id found returned from agent"
        print(interactable.dendrite_id)
        tag = soup_without_hidden_elements.find(
            attrs={"d-id": interactable.dendrite_id}
        )
        if isinstance(tag, Tag):
            selector = find_css_selector(tag, soup)
            cache = config.element_cache
            await add_selector_to_cache(
                prompt,
                bs4_selector=selector,
                url=dto.page_information.url,
                cache=cache,
            )
            return GetElementResponse(
                selectors=[selector],
                message=interactable.reason,
                d_id=interactable.dendrite_id,
                status="success",
            )
        interactable.status = "failed"
        interactable.reason = "d-id does not exist in the soup"

    return GetElementResponse(
        message=interactable.reason,
        status=interactable.status,
    )


async def get_cached_selector(dto: CachedSelectorDTO, config: Config) -> List[Selector]:
    if not isinstance(dto.prompt, str):
        return []
    db_selectors = await get_selector_from_cache(
        dto.url, dto.prompt, config.element_cache
    )

    if db_selectors is None:
        return []

    return db_selectors


# async def check_cache(
#     soup: BeautifulSoup, url: str, prompt: str, only_one: bool, config: Config
# ) -> Optional[GetElementResponse]:
#     cache = config.element_cache
#     db_selectors = await get_selector_from_cache(url, prompt, cache)

#     if db_selectors is None:
#         return None

#     if check_if_selector_successful(db_selectors.selector, soup, only_one):
#         return GetElementResponse(
#             selectors=[db_selectors.selector],
#             status="success",
#         )


# async def get_cached_selector(dto: GetCachedSelectorDTO) -> Optional[Selector]:
#     cache = config.element_cache
#     db_selectors = await get_selector_from_cache(dto.url, dto.prompt, cache)
#     return db_selectors
