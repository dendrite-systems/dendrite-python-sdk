from typing import Optional

from bs4 import BeautifulSoup, Tag
from loguru import logger


def find_css_selector(ele: Tag, soup: BeautifulSoup) -> str:
    logger.debug(f"Finding selector for element: {ele.name} with attrs: {ele.attrs}")

    # Add this debug block
    final_selector = ""  # Track the selector being built
    matches = []  # Track matching elements

    def debug_selector(selector: str) -> None:
        nonlocal matches
        try:
            matches = soup.select(selector)
            logger.debug(f"Selector '{selector}' matched {len(matches)} elements")
        except Exception as e:
            logger.error(f"Invalid selector '{selector}': {e}")

    # Check for inherently unique elements
    if ele.name in ["html", "head", "body"]:
        return ele.name

    # List of attributes to check for unique selectors
    priority_attrs = [
        "id",
        "name",
        "data-testid",
        "data-cy",
        "data-qa",
        "aria-label",
        "aria-labelledby",
        "for",
        "href",
        "alt",
        "title",
        "role",
        "placeholder",
    ]

    # Try attrs
    for attr in priority_attrs:
        if attr_selector := check_unique_attribute(ele, soup, attr, ele.name):
            return attr_selector

    # Try class combinations
    if class_selector := find_unique_class_combination(ele, soup):
        return class_selector

    # If still not unique, use parent selector with nth-child
    parent_selector = find_selector_with_parent(ele, soup)

    return parent_selector


def check_unique_attribute(
    ele: Tag, soup: BeautifulSoup, attr: str, tag_name: str
) -> str:
    attr_value = ele.get(attr)
    if attr_value:
        attr_value = css_escape(attr_value)
        attr = css_escape(attr)
        selector = f'{css_escape(tag_name)}[{attr}="{attr_value}"]'
        if check_if_selector_successful(selector, soup, True):
            return selector
    return ""


def find_unique_class_combination(ele: Tag, soup: BeautifulSoup) -> str:
    classes = ele.get("class", [])

    if isinstance(classes, str):
        classes = [classes]

    if not classes:
        return ""

    tag_name = css_escape(ele.name)

    # Try single classes first
    for cls in classes:
        selector = f"{tag_name}.{css_escape(cls)}"
        if check_if_selector_successful(selector, soup, True):
            return selector

    # If single classes don't work, try the full combination
    full_selector = f"{tag_name}{'.'.join([''] + [css_escape(c) for c in classes])}"
    if check_if_selector_successful(full_selector, soup, True):
        return full_selector

    return ""


def find_selector_with_parent(ele: Tag, soup: BeautifulSoup) -> str:
    parent = ele.find_parent()
    if parent is None or parent == soup:
        return f"{css_escape(ele.name)}"

    parent_selector = find_css_selector(parent, soup)
    siblings_of_same_type = parent.find_all(ele.name, recursive=False)

    if len(siblings_of_same_type) == 1:
        return f"{parent_selector} > {css_escape(ele.name)}"
    else:
        index = position_in_node_list(ele, parent)
        return f"{parent_selector} > {css_escape(ele.name)}:nth-child({index})"


def position_in_node_list(element: Tag, parent: Tag):
    for index, child in enumerate(parent.find_all(recursive=False)):
        if child == element:
            return index + 1
    return -1


# https://github.com/mathiasbynens/CSS.escape
def css_escape(value):
    if len(str(value)) == 0:
        raise TypeError("`CSS.escape` requires an argument.")

    string = str(value)
    length = len(string)
    result = ""
    first_code_unit = ord(string[0]) if length > 0 else None

    if length == 1 and first_code_unit == 0x002D:
        return "\\" + string

    for index in range(length):
        code_unit = ord(string[index])

        if code_unit == 0x0000:
            result += "\uFFFD"
            continue

        if (
            (0x0001 <= code_unit <= 0x001F)
            or code_unit == 0x007F
            or (index == 0 and 0x0030 <= code_unit <= 0x0039)
            or (
                index == 1
                and 0x0030 <= code_unit <= 0x0039
                and first_code_unit == 0x002D
            )
        ):
            result += "\\" + format(code_unit, "x") + " "
            continue

        if (
            code_unit >= 0x0080
            or code_unit == 0x002D
            or code_unit == 0x005F
            or 0x0030 <= code_unit <= 0x0039
            or 0x0041 <= code_unit <= 0x005A
            or 0x0061 <= code_unit <= 0x007A
        ):
            result += string[index]
            continue

        result += "\\" + string[index]

    return result


def check_if_selector_successful(
    selector: str,
    bs4: BeautifulSoup,
    only_one: bool,
) -> Optional[str]:

    els = None
    try:
        els = bs4.select(selector)
    except Exception as e:
        logger.warning(f"Error selecting {selector}: {e}")

    if els:
        if only_one and len(els) == 1:
            return selector
        elif not only_one and len(els) >= 1:
            return selector

    return None
