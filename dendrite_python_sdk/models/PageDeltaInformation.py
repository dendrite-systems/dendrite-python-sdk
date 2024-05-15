from pydantic import BaseModel
from dendrite_python_sdk.models.PageInformation import PageInformation


class PageDeltaInformation(BaseModel):
    page_before: PageInformation
    page_after: PageInformation
