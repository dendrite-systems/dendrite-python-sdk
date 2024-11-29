from pydantic import BaseModel


class PageInformation(BaseModel):
    url: str
    raw_html: str
    screenshot_base64: str
    time_since_frame_navigated: float


class PageDiffInformation(BaseModel):
    screenshot_before: str
    screenshot_after: str
    page_before: PageInformation
    page_after: PageInformation
