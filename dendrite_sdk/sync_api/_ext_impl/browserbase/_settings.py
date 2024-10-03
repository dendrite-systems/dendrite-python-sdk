from pydantic import BaseModel


class BrowserBaseSettings(BaseModel):
    api_key: str
    project_id: str
    enable_proxy: bool = False
    enable_stealth: bool = True
