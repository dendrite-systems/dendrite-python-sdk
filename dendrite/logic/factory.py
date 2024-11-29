# from typing import Literal, Optional

# from dendrite.logic.interfaces.async_api import LogicAPIProtocol


# class BrowserAPIFactory:
#     @staticmethod
#     def create_browser_api(
#         mode: Literal["local", "remote"],
#         session_id: Optional[str] = None
#     ) -> LogicAPIProtocol':
#         if mode == "local":
#             return LocalBrowserAPI()
#         else:
#             return BrowserAPIClient(api_config, session_id)
