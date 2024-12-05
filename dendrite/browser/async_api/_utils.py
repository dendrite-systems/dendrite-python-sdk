import inspect
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import tldextract
from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import Error, Frame
from pydantic import BaseModel

from dendrite.models.selector import Selector

from .dendrite_element import AsyncElement
from .types import PlaywrightPage, TypeSpec

if TYPE_CHECKING:
    from .dendrite_page import AsyncPage

from dendrite.logic.dom.strip import mild_strip_in_place

from .js import GENERATE_DENDRITE_IDS_IFRAME_SCRIPT


def get_domain_w_suffix(url: str) -> str:
    parsed_url = tldextract.extract(url)
    if parsed_url.suffix == "":
        raise ValueError(f"Invalid URL: {url}")

    return f"{parsed_url.domain}.{parsed_url.suffix}"


async def expand_iframes(
    page: PlaywrightPage,
    page_soup: BeautifulSoup,
):
    async def get_iframe_path(frame: Frame):
        path_parts = []
        current_frame = frame
        while current_frame.parent_frame is not None:
            iframe_element = await current_frame.frame_element()
            iframe_id = await iframe_element.get_attribute("d-id")
            if iframe_id is None:
                # If any iframe_id in the path is None, we cannot build the path
                return None
            path_parts.insert(0, iframe_id)
            current_frame = current_frame.parent_frame
        return "|".join(path_parts)

    for frame in page.frames:
        if frame.parent_frame is None:
            continue  # Skip the main frame
        try:
            iframe_element = await frame.frame_element()

            iframe_id = await iframe_element.get_attribute("d-id")
            if iframe_id is None:
                continue
            iframe_path = await get_iframe_path(frame)
        except Error as e:
            continue

        if iframe_path is None:
            continue

        try:
            await frame.evaluate(
                GENERATE_DENDRITE_IDS_IFRAME_SCRIPT, {"frame_path": iframe_path}
            )
            frame_content = await frame.content()
            frame_tree = BeautifulSoup(frame_content, "lxml")
            mild_strip_in_place(frame_tree)
            merge_iframe_to_page(iframe_id, page_soup, frame_tree)
        except Error as e:
            continue


def merge_iframe_to_page(
    iframe_id: str,
    page: BeautifulSoup,
    iframe: BeautifulSoup,
):
    iframe_element = page.find("iframe", {"d-id": iframe_id})
    if iframe_element is None:
        logger.debug(f"Could not find iframe with ID {iframe_id} in page soup")
        return

    iframe_element.replace_with(iframe)


async def _get_all_elements_from_selector_soup(
    selector: str, soup: BeautifulSoup, page: "AsyncPage"
) -> List[AsyncElement]:
    dendrite_elements: List[AsyncElement] = []

    elements = soup.select(selector)

    for element in elements:
        frame = page._get_context(element)
        d_id = element.get("d-id", "")
        locator = frame.locator(f"xpath=//*[@d-id='{d_id}']")

        if not d_id:
            continue

        if isinstance(d_id, list):
            d_id = d_id[0]
        dendrite_elements.append(
            AsyncElement(d_id, locator, page.dendrite_browser, page._browser_api_client)
        )

    return dendrite_elements


async def get_elements_from_selectors_soup(
    page: "AsyncPage",
    soup: BeautifulSoup,
    selectors: List[Selector],
    only_one: bool,
) -> Union[Optional[AsyncElement], List[AsyncElement]]:

    for selector in reversed(selectors):
        dendrite_elements = await _get_all_elements_from_selector_soup(
            selector.selector, soup, page
        )

        if len(dendrite_elements) > 0:
            return dendrite_elements[0] if only_one else dendrite_elements

    return None


def to_json_schema(type_spec: TypeSpec) -> Dict[str, Any]:
    if isinstance(type_spec, dict):
        # Assume it's already a JSON schema
        return type_spec
    if inspect.isclass(type_spec) and issubclass(type_spec, BaseModel):
        # Convert Pydantic model to JSON schema
        return type_spec.model_json_schema()
    if type_spec in (bool, int, float, str):
        # Convert basic Python types to JSON schema
        type_map = {bool: "boolean", int: "integer", float: "number", str: "string"}
        return {"type": type_map[type_spec]}

    raise ValueError(f"Unsupported type specification: {type_spec}")


def convert_to_type_spec(type_spec: TypeSpec, return_data: Any) -> TypeSpec:
    if isinstance(type_spec, type):
        if issubclass(type_spec, BaseModel):
            return type_spec.model_validate(return_data)
        if type_spec in (str, float, bool, int):
            return type_spec(return_data)

        raise ValueError(f"Unsupported type: {type_spec}")
    if isinstance(type_spec, dict):
        return return_data

    raise ValueError(f"Unsupported type specification: {type_spec}")
