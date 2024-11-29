from pydantic import BaseModel


class Selector(BaseModel):
    selector: str
    prompt: str
    url: str
    netloc: str
    created_at: str
