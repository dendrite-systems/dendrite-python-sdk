from bs4 import BeautifulSoup, Doctype, Tag, Comment


def mild_strip(soup: Tag, keep_d_id: bool = True) -> BeautifulSoup:
    new_soup = BeautifulSoup(str(soup), "html.parser")
    _mild_strip(new_soup, keep_d_id)
    return new_soup


def mild_strip_in_place(soup: BeautifulSoup, keep_d_id: bool = True) -> None:
    _mild_strip(soup, keep_d_id)


def _mild_strip(soup: BeautifulSoup, keep_d_id: bool = True) -> None:
    for element in soup(text=lambda text: isinstance(text, Comment)):
        element.extract()
    for tag in soup(
        ["head", "script", "style", "path", "polygon", "defs", "svg", "br", "Doctype"]
    ):
        tag.extract()
    for element in soup.contents:
        if isinstance(element, Doctype):
            element.extract()
    for tag in soup.find_all(True):
        if tag.attrs.get("is-interactable-d_id") == "true":
            continue
        tag.attrs = {
            attr: value[:100] if isinstance(value, str) else value
            for (attr, value) in tag.attrs.items()
        }
        if keep_d_id == False:
            del tag["d-id"]
