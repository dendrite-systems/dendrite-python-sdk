from pydantic import BaseModel


class Script(BaseModel):
    url: str
    domain: str
    script: str
    created_at: str
