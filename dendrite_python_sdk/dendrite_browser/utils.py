from typing import Union
from playwright.async_api import Page, Frame, FrameLocator, ElementHandle
from bs4 import BeautifulSoup, Tag
from loguru import logger

from dendrite_python_sdk.dendrite_browser.scripts import (
    TEST_GEN_IDS_SCRIPT,
)
from dendrite_python_sdk.dendrite_browser.dom_util.mild_strip import mild_strip_in_place


async def expand_iframes(
    page: Page,
    page_soup: BeautifulSoup,
    iframe_path: str = "",
    frame: Union[ElementHandle, None] = None,
):
    # logger.debug(f"New iterations")
    if frame is None:
        iframes = await page.query_selector_all("iframe")
    else:
        content_frame = await frame.content_frame()
        if not content_frame:
            return
        iframes = await content_frame.query_selector_all("iframe")
    for iframe in iframes:
        # TODO: kolla om iframe inte har doc eller body, skippa då

        iframe_id = await iframe.get_attribute("d-id")
        if iframe_id is None:
            continue

        new_iframe_path = ""
        if iframe_path:
            new_iframe_path = f"{iframe_path}|"
        new_iframe_path = f"{new_iframe_path}{iframe_id}"

        content_frame = await iframe.content_frame()
        if content_frame is None:
            continue

        await content_frame.evaluate(
            TEST_GEN_IDS_SCRIPT, {"frame_path": new_iframe_path}
        )

        frame_content = await content_frame.content()
        # logger.debug(f"Expanding iframe path: {new_iframe_path} url : {content_frame.url}")

        frame_tree = BeautifulSoup(frame_content, "html.parser")
        mild_strip_in_place(frame_tree)
        merge_iframe_to_page(iframe_id, page_soup, frame_tree)
        await expand_iframes(
            page,
            page_soup,
            new_iframe_path,
            iframe,
        )


def merge_iframe_to_page(
    iframe_id: str,
    page_accessibility_tree: BeautifulSoup,
    iframe_accessibility_tree: BeautifulSoup,
):
    iframe_element = page_accessibility_tree.find("iframe", {"d-id": iframe_id})
    if iframe_element is None:
        logger.debug(f"Could not find iframe with ID {iframe_id} in page soup")
        return

    # iframe_url = iframe_element.get('src', 'URL not found')
    # comment = page_accessibility_tree.new_string(f"<!-- Iframe URL: {iframe_url} -->", Comment)

    # Insert the comment before the iframe content
    # iframe_accessibility_tree.append(comment)

    iframe_element.replace_with(iframe_accessibility_tree)


def get_frame_context(page: Page, iframe_path: str) -> Union[FrameLocator, Page]:
    iframe_path_list = iframe_path.split("|")
    frame_context = page
    for iframe_id in iframe_path_list:
        frame_context = frame_context.frame_locator(f"[tf623_id='{iframe_id}']")
    return frame_context


def get_describing_attrs(bs4: Tag):
    salient_attributes = [
        "alt",
        "aria-describedby",
        "aria-label",
        "aria-role",
        "input-checked",
        "label",
        "name",
        "option_selected",
        "placeholder",
        "readonly",
        "text-value",
        "title",
        "value",
        "type",
        "href",
        "role",
        "data-hidden",
    ]
    res = []
    for attr in salient_attributes:
        attribute_value = bs4.get(attr, None)
        if attribute_value:
            res.append(f"{attr}: {attribute_value}")

    if len(res) == 0:
        res += [
            f"{key}: {str(val)}"
            for key, val in list(bs4.attrs.items())[:3]
            if key != "d-id"
        ]

    return ", ".join(res)
