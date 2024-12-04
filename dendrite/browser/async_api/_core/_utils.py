from typing import TYPE_CHECKING, List, Optional, Union

from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import ElementHandle, Error, Frame, FrameLocator

from dendrite.browser.async_api._core._type_spec import PlaywrightPage
from dendrite.browser.async_api._core.dendrite_element import AsyncElement
from dendrite.browser.async_api._core.models.response import AsyncElementsResponse
from dendrite.models.response.get_element_response import GetElementResponse
from dendrite.models.selector import Selector

if TYPE_CHECKING:
    from dendrite.browser.async_api._core.dendrite_page import AsyncPage

from dendrite.browser.async_api._core._js import GENERATE_DENDRITE_IDS_IFRAME_SCRIPT
from dendrite.logic.dom.strip import mild_strip_in_place

import os
import platform
from pathlib import Path


def get_chrome_user_data_dir() -> str:
    """
    Get the default Chrome user data directory based on the operating system.

    Returns:
        str: Path to Chrome user data directory
    """
    system = platform.system()
    home = Path.home()

    if system == "Windows":
        return str(Path(os.getenv("LOCALAPPDATA", "")) / "Google/Chrome/User Data")
    elif system == "Darwin":  # macOS
        return str(home / "Library/Application Support/Google/Chrome/")
    elif system == "Linux":
        return str(home / ".config/google-chrome")
    else:
        raise NotImplementedError(f"Unsupported operating system: {system}")


def chrome_profile_exists() -> bool:
    """Check if a Chrome profile exists in the default location."""
    try:
        user_data_dir = get_chrome_user_data_dir()
        return Path(user_data_dir).exists()
    except:
        return False


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
            logger.debug(f"Error processing frame {iframe_id}: {e}")
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
