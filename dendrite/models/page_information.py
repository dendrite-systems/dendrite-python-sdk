from anthropic import BaseModel


class PageInformation(BaseModel):
    url: str
    raw_html: str
    screenshot_base64: str
    time_since_frame_navigated: float
