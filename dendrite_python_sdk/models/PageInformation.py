from typing import Dict, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel


class InteractableElementInfo(TypedDict):
    attrs: Optional[str]
    text: Optional[str]


class PageInformation(BaseModel):
    url: str
    raw_html: str
    interactable_element_info: Dict[str, InteractableElementInfo]
    screenshot_base64: str
