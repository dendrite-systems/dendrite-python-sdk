from typing import TYPE_CHECKING, List, Optional, Union
from bs4 import BeautifulSoup
from loguru import logger
from playwright.sync_api import ElementHandle, Error, Frame, FrameLocator
from dendrite.browser.sync_api._core._type_spec import PlaywrightPage
from dendrite.browser.sync_api._core.dendrite_element import Element
from dendrite.browser.sync_api._core.models.response import ElementsResponse
from dendrite.models.response.get_element_response import GetElementResponse
from dendrite.models.selector import Selector

if TYPE_CHECKING:
    from dendrite.browser.sync_api._core.dendrite_page import Page
from dendrite.browser.sync_api._core._js import GENERATE_DENDRITE_IDS_IFRAME_SCRIPT
from dendrite.logic.dom.strip import mild_strip_in_place


def expand_iframes(page: PlaywrightPage, page_soup: BeautifulSoup):

    def get_iframe_path(frame: Frame):
        path_parts = []
        current_frame = frame
        while current_frame.parent_frame is not None:
            iframe_element = current_frame.frame_element()
            iframe_id = iframe_element.get_attribute("d-id")
            if iframe_id is None:
                return None
            path_parts.insert(0, iframe_id)
            current_frame = current_frame.parent_frame
        return "|".join(path_parts)

    for frame in page.frames:
        if frame.parent_frame is None:
            continue
        try:
            iframe_element = frame.frame_element()
            iframe_id = iframe_element.get_attribute("d-id")
            if iframe_id is None:
                continue
            iframe_path = get_iframe_path(frame)
        except Error as e:
            continue
        if iframe_path is None:
            continue
        try:
            frame.evaluate(
                GENERATE_DENDRITE_IDS_IFRAME_SCRIPT, {"frame_path": iframe_path}
            )
            frame_content = frame.content()
            frame_tree = BeautifulSoup(frame_content, "lxml")
            mild_strip_in_place(frame_tree)
            merge_iframe_to_page(iframe_id, page_soup, frame_tree)
        except Error as e:
            logger.debug(f"Error processing frame {iframe_id}: {e}")
            continue


def merge_iframe_to_page(iframe_id: str, page: BeautifulSoup, iframe: BeautifulSoup):
    iframe_element = page.find("iframe", {"d-id": iframe_id})
    if iframe_element is None:
        logger.debug(f"Could not find iframe with ID {iframe_id} in page soup")
        return
    iframe_element.replace_with(iframe)


def _get_all_elements_from_selector_soup(
    selector: str, soup: BeautifulSoup, page: "Page"
) -> List[Element]:
    dendrite_elements: List[Element] = []
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
            Element(d_id, locator, page.dendrite_browser, page._browser_api_client)
        )
    return dendrite_elements


def get_elements_from_selectors_soup(
    page: "Page", soup: BeautifulSoup, selectors: List[Selector], only_one: bool
) -> Union[Optional[Element], List[Element]]:
    for selector in reversed(selectors):
        dendrite_elements = _get_all_elements_from_selector_soup(
            selector.selector, soup, page
        )
        if len(dendrite_elements) > 0:
            return dendrite_elements[0] if only_one else dendrite_elements
    return None
