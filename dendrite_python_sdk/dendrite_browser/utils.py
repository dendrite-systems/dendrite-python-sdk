from typing import Dict, Optional, Tuple, Union
from typing_extensions import TypedDict
from playwright.async_api import Page
from bs4 import BeautifulSoup, Tag


class InteractableElementRes(TypedDict):
    attrs: Optional[str]
    text: Optional[str]


async def get_interactive_elements_with_playwright(
    page: Page,
) -> Dict[str, InteractableElementRes]:
    result_outerhtml = await page.evaluate(
        """() => {
        const selectors = [
            'a', 'button', 'input', 'select', 'textarea', 'adc-tab', '[role="button"]',
            '[role="radio"]', '[role="option"]', '[role="combobox"]', '[role="textbox"]',
            '[role="listbox"]', '[role="menu"]', '[type="button"]', '[type="radio"]',
            '[type="combobox"]', '[type="textbox"]', '[type="listbox"]', '[type="menu"]',
            '[tabindex]:not([tabindex="-1"])', '[contenteditable]:not([contenteditable="false"])',
            '[onclick]', '[onfocus]', '[onkeydown]', '[onkeypress]', '[onkeyup]', "[checkbox]",
            '[aria-disabled="false"],[data-link]', '[href]'
        ];
        let elements = document.querySelectorAll(selectors.join(','));
        return Array.from(elements).map(el => el.outerHTML);
    }"""
    )

    res: Dict[str, InteractableElementRes] = {}
    for outerhtml in result_outerhtml:
        info = extract_info(outerhtml)
        if info:
            res[info[0]] = info[1]
    return res


def extract_info(outerhtml: str) -> Union[Tuple[str, InteractableElementRes], None]:
    bs4_tag = BeautifulSoup(outerhtml, "html.parser")
    bs4_tag = bs4_tag.contents[0]
    if isinstance(bs4_tag, Tag):
        id = bs4_tag.get("d-id", None)
        desc = get_describing_attrs(bs4_tag)
        if id:
            if bs4_tag.text and bs4_tag.text.strip() != "":
                return (str(id), {"text": bs4_tag.text.strip(), "attrs": desc})
            else:
                desc = get_describing_attrs(bs4_tag)
                return (str(id), {"attrs": desc, "text": None})

    return None


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
