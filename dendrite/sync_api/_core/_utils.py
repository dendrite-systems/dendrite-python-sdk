from typing import Union, List, TYPE_CHECKING
from playwright.sync_api import FrameLocator, ElementHandle, Error
from bs4 import BeautifulSoup
from loguru import logger
from dendrite.sync_api._core._type_spec import PlaywrightPage
from dendrite.sync_api._core.dendrite_element import Element

if TYPE_CHECKING:
    from dendrite.sync_api._core.dendrite_page import Page
from dendrite.sync_api._core._js import GENERATE_DENDRITE_IDS_IFRAME_SCRIPT
from dendrite.sync_api._dom.util.mild_strip import mild_strip_in_place


def expand_iframes(
    page: PlaywrightPage,
    page_soup: BeautifulSoup,
    iframe_path: str = "",
    frame: Union[ElementHandle, None] = None,
):
    if frame is None:
        iframes = page.query_selector_all("iframe")
    else:
        content_frame = frame.content_frame()
        if not content_frame:
            return
        iframes = content_frame.query_selector_all("iframe")
    for iframe in iframes:
        iframe_id = iframe.get_attribute("d-id")
        if iframe_id is None:
            continue
        new_iframe_path = ""
        if iframe_path:
            new_iframe_path = f"{iframe_path}|"
        new_iframe_path = f"{new_iframe_path}{iframe_id}"
        try:
            content_frame = iframe.content_frame()
            if content_frame is None:
                continue
            content_frame.evaluate(
                GENERATE_DENDRITE_IDS_IFRAME_SCRIPT, {"frame_path": new_iframe_path}
            )
            frame_content = content_frame.content()
            frame_tree = BeautifulSoup(frame_content, "html.parser")
            mild_strip_in_place(frame_tree)
            merge_iframe_to_page(iframe_id, page_soup, frame_tree)
            expand_iframes(page, page_soup, new_iframe_path, iframe)
        except Error as e:
            logger.debug(f"Error getting content frame for iframe {iframe_id}: {e}")
            continue


def merge_iframe_to_page(iframe_id: str, page: BeautifulSoup, iframe: BeautifulSoup):
    iframe_element = page.find("iframe", {"d-id": iframe_id})
    if iframe_element is None:
        logger.debug(f"Could not find iframe with ID {iframe_id} in page soup")
        return
    iframe_element.replace_with(iframe)


def get_frame_context(
    page: PlaywrightPage, iframe_path: str
) -> Union[FrameLocator, PlaywrightPage]:
    iframe_path_list = iframe_path.split("|")
    frame_context = page
    for iframe_id in iframe_path_list:
        frame_context = frame_context.frame_locator(f"[tf623_id='{iframe_id}']")
    return frame_context
