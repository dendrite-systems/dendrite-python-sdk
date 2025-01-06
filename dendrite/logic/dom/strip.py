import copy
from typing import List, Union, overload

from bs4 import BeautifulSoup, Comment, Doctype, Tag


def mild_strip(soup: Tag, keep_d_id: bool = True) -> BeautifulSoup:
    new_soup = BeautifulSoup(str(soup), "html.parser")
    _mild_strip(new_soup, keep_d_id)
    return new_soup


def mild_strip_in_place(soup: BeautifulSoup, keep_d_id: bool = True) -> None:
    _mild_strip(soup, keep_d_id)


def _mild_strip(soup: BeautifulSoup, keep_d_id: bool = True) -> None:
    for element in soup(text=lambda text: isinstance(text, Comment)):
        element.extract()

    # for text in soup.find_all(text=lambda text: isinstance(text, NavigableString)):
    #     if len(text) > 200:
    #         text.replace_with(text[:200] + f"... [{len(text)-200} more chars]")

    for tag in soup(
        ["head", "script", "style", "path", "polygon", "defs", "svg", "br", "Doctype"]
    ):
        tag.extract()

    for element in soup.contents:
        if isinstance(element, Doctype):
            element.extract()

    # for tag in soup.find_all(True):
    #     tag.attrs = {
    #         attr: (value[:100] if isinstance(value, str) else value)
    #         for attr, value in tag.attrs.items()
    #     }
    #     if keep_d_id == False:
    #         del tag["d-id"]
    for tag in soup.find_all(True):
        if tag.attrs.get("is-interactable-d_id") == "true":
            continue

        tag.attrs = {
            attr: (value[:100] if isinstance(value, str) else value)
            for attr, value in tag.attrs.items()
        }
        if keep_d_id == False:
            del tag["d-id"]

    # if browser != None:
    #     for elem in list(soup.descendants):
    #         if isinstance(elem, Tag) and not browser.element_is_visible(elem):
    #             elem.extract()


@overload
def shorten_attr_val(value: str, limit: int = 50) -> str: ...


@overload
def shorten_attr_val(value: List[str], limit: int = 50) -> List[str]: ...


def shorten_attr_val(
    value: Union[str, List[str]], limit: int = 50
) -> Union[str, List[str]]:
    if isinstance(value, str):
        return value[:limit]

    char_count = sum(map(len, value))
    if char_count <= limit:
        return value

    while len(value) > 1 and char_count > limit:
        char_count -= len(value.pop())

    if len(value) == 1:
        return value[0][:limit]

    return value


def clear_attrs(element: Tag):

    salient_attributes = [
        "d-id",
        "class",
        "id",
        "type",
        "alt",
        "aria-describedby",
        "aria-label",
        "contenteditable",
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
        "href",
        "role",
        "action",
        "method",
    ]
    attrs = {
        attr: shorten_attr_val(value, limit=200)
        for attr, value in element.attrs.items()
        if attr in salient_attributes
    }
    element.attrs = attrs


def strip_soup(soup: BeautifulSoup) -> BeautifulSoup:
    # Create a copy of the soup to avoid modifying the original
    stripped_soup = BeautifulSoup(str(soup), "html.parser")

    for tag in stripped_soup(
        [
            "head",
            "script",
            "style",
            "path",
            "polygon",
            "defs",
            "br",
            "Doctype",
        ]  # add noscript?
    ):
        tag.extract()

    # Remove comments
    comments = stripped_soup.find_all(text=lambda text: isinstance(text, Comment))
    for comment in comments:
        comment.extract()

    # Clear non-salient attributes
    for element in stripped_soup.find_all(True):
        if isinstance(element, Doctype):
            element.extract()
        else:
            clear_attrs(element)

    return stripped_soup


def remove_hidden_elements(soup: BeautifulSoup):
    # data-hidden is added by DendriteBrowser when an element is not visible
    new_soup = copy.copy(soup)
    elems = new_soup.find_all(attrs={"data-hidden": True})
    for elem in elems:
        elem.extract()
    return new_soup
