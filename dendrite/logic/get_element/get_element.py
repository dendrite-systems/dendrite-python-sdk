from typing import Optional

from bs4 import BeautifulSoup, Tag
from loguru import logger
from pydantic import BaseModel

from dendrite.logic.cache.file_cache import FileCache
from dendrite.logic.config import config
from dendrite.logic.dom.css import check_if_selector_successful, find_css_selector
from dendrite.logic.dom.strip import remove_hidden_elements
from dendrite.logic.get_element.cached_selector import (
    add_selector_to_cache,
    get_selector_from_cache,
)
from dendrite.models.dto.get_elements_dto import GetElementsDTO
from dendrite.models.page_information import PageInformation
from dendrite.models.response.get_element_response import GetElementResponse
from dendrite.models.selector import Selector

from .hanifi_search import hanifi_search




async def get_element(dto: GetElementsDTO) -> GetElementResponse:

    if isinstance(dto.prompt, str):
        return await process_prompt(dto.prompt, dto)
    raise ...

async def process_prompt(
   prompt: str, dto: GetElementsDTO
) -> GetElementResponse:

    soup = BeautifulSoup(dto.page_information.raw_html, "lxml")

    if dto.use_cache:
        res = await check_cache(
            soup,
            dto.page_information.url,
            prompt,
            dto.only_one,
        )
        if res:
            return res

    if dto.force_use_cache:
        return GetElementResponse(
            selectors=[],
            status="failed",
            message="Forced to use cache, but no cached selectors found",
            used_cache=False,
        )

    return await get_new_element(soup, prompt, dto )

async def get_new_element(soup: BeautifulSoup, prompt: str, dto: GetElementsDTO) -> GetElementResponse:
    soup_without_hidden_elements = remove_hidden_elements(soup)
    element = await hanifi_search(
            soup_without_hidden_elements,
            prompt,
            dto.page_information.time_since_frame_navigated,
        )
    interactable = element[0]

    if interactable.status == "success":
        if interactable.dendrite_id is None:
            interactable.status = "failed"
            interactable.reason = "No d-id found returned from agent"
        tag = soup.find(attrs={"d-id": interactable.dendrite_id})
        if isinstance(tag, Tag):
            selector = find_css_selector(tag, soup)
            await add_selector_to_cache(
                prompt,
                bs4_selector=selector,
                url=dto.page_information.url,
            )
            return GetElementResponse(
                selectors=[selector],
                message=interactable.reason,
                d_id=interactable.dendrite_id,
                status="success",
                used_cache=False,
            )
        interactable.status = "failed"
        interactable.reason = "d-id does not exist in the soup"

    return GetElementResponse(
        message=interactable.reason,
        status=interactable.status,
        used_cache=False,
    )


async def check_cache(
    soup: BeautifulSoup, url: str, prompt: str, only_one: bool
) -> Optional[GetElementResponse]:
    cache = config.element_cache
    db_selectors = await get_selector_from_cache(url, prompt, cache)

    if db_selectors is None:
        return None

    successful_selectors = []

    if check_if_selector_successful(db_selectors.selector, soup, only_one):
        return GetElementResponse(
            selectors=successful_selectors,
            status="success",
            used_cache=True,
        )

