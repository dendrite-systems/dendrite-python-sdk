import os
from typing import Optional

from dendrite.exceptions import MissingApiKeyError


class BrowserbaseConfig:
    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        enable_proxy: bool = False,
    ):
        api_key = api_key if api_key is not None else os.getenv("BROWSERBASE_API_KEY")
        if api_key is None:
            raise MissingApiKeyError("BROWSERBASE_API_KEY")
        project_id = (
            project_id
            if project_id is not None
            else os.getenv("BROWSERBASE_PROJECT_ID")
        )
        if project_id is None:
            raise MissingApiKeyError("BROWSERBASE_PROJECT_ID")

        self.api_key = api_key
        self.project_id = project_id
        self.enable_proxy = enable_proxy
