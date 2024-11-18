
from typing import Optional
from anthropic import BaseModel
from bs4 import BeautifulSoup, Tag
from loguru import logger
from dendrite.browser.async_api._core.models.api_config import APIConfig
from dendrite.browser.async_api._core.models.page_information import PageInformation
from dendrite.browser.sync_api._api.response.get_element_response import GetElementResponse
from dendrite.logic.interfaces.cache import CacheProtocol
from dendrite.logic.local.dom.css import check_if_selector_successful, find_css_selector
from .hanifi_search import hanifi_search
from dendrite.logic.local.get_element.cached_selector import add_selector_in_db, get_selector_from_db
from dendrite.logic.local.get_element.dom import remove_hidden_elements


class GetElementDTO(BaseModel):
    page_information: PageInformation
    prompt: str
    api_config: APIConfig
    use_cache: bool = True
    only_one: bool
    force_use_cache: bool = False


async def process_single_prompt(
    get_elements_dto: GetElementDTO, prompt: str, user_id: str, cache: Optional[CacheProtocol] = None
) -> GetElementResponse:
     
    soup = BeautifulSoup(get_elements_dto.page_information.raw_html, "lxml")

    if get_elements_dto.use_cache and cache:
        res = await check_cache(soup, get_elements_dto.page_information.url, prompt, get_elements_dto.only_one, cache)
        if res:
            return res


    if get_elements_dto.force_use_cache:
        return GetElementResponse(
            selectors=[],
            status="failed",
            message="Forced to use cache, but no cached selectors found",
            used_cache=False,
        )

    soup_without_hidden_elements = remove_hidden_elements(soup)

    if get_elements_dto.only_one:
        interactables_res = await hanifi_search(
            soup_without_hidden_elements,
            prompt,
            get_elements_dto.api_config,
            get_elements_dto.page_information.time_since_frame_navigated,
        )
        interactable = interactables_res[0]

        if interactable.status == "success":
            tag = soup.find(attrs={"d-id": interactable.dendrite_id})
            if isinstance(tag, Tag):
                selector = find_css_selector(tag, soup)
                await add_selector_in_db(
                    prompt,
                    bs4_selector=selector,
                    url=get_elements_dto.page_information.url,
                )
                return GetElementResponse(
                    selectors=[selector],
                    message=interactable.reason,
                    status="success",
                    used_cache=False,
                )
        else:
            return GetElementResponse(
                message=interactable.reason,
                status=interactable.status,
                used_cache=False,
            )


async def get_element_selector_action(
    get_elements_dto: GetElementDTO, user_id: str
) -> GetElementResponse:
    return await process_single_prompt(
        get_elements_dto, get_elements_dto.prompt, user_id
    )

async def check_cache(soup: BeautifulSoup, url: str, prompt: str, only_one: bool, cache: CacheProtocol) -> Optional[GetElementResponse]:
    db_selectors = await get_selector_from_db(
        url, prompt, cache
    )

    if db_selectors is None:
        return None
    
    successful_selectors = []

    if check_if_selector_successful(db_selectors.selector, soup, only_one):
        return GetElementResponse(
            selectors=successful_selectors,
            status="success",
            used_cache=True,
            )
