
from typing import Literal, Optional

from dendrite.logic.interfaces.async_api import BrowserAPIProtocol


class BrowserAPIFactory:
    @staticmethod
    def create_browser_api(
        mode: Literal["local", "remote"],
        api_config: APIConfig,
        session_id: Optional[str] = None
    ) -> BrowserAPIProtocol:
        if mode == "local":
            return LocalBrowserAPI()
        else:
            return BrowserAPIClient(api_config, session_id)