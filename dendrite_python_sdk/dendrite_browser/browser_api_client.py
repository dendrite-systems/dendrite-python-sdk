import json
import sys
from typing import Optional, Union
import httpx
from dendrite_python_sdk.dendrite_browser.authentication.auth_session import AuthSession
from dendrite_python_sdk.dto.AskPageDTO import AskPageDTO
from dendrite_python_sdk.dto.AuthenticateDTO import AuthenticateDTO
from dendrite_python_sdk.dto.GetElementsDTO import GetElementsDTO
from dendrite_python_sdk.dto.MakeInteractionDTO import MakeInteractionDTO
from dendrite_python_sdk.dto.ScrapePageDTO import ScrapePageDTO
from dendrite_python_sdk.dto.TryRunScriptDTO import TryRunScriptDTO
from dendrite_python_sdk.dto.UploadAuthSessionDTO import UploadAuthSessionDTO
from dendrite_python_sdk.responses.AskPageResponse import AskPageResponse
from dendrite_python_sdk.responses.InteractionResponse import InteractionResponse
from dendrite_python_sdk.responses.ScrapePageResponse import ScrapePageResponse
from dendrite_python_sdk.dendrite_browser.HTTPClient import HTTPClient


class BrowserAPIClient(HTTPClient):

    async def authenticate(self, dto: AuthenticateDTO):
        res = await self.send_request(
            "actions/authenticate", data=dto.dict(), method="POST"
        )
        return AuthSession(**res)

    async def upload_auth_session(self, dto: UploadAuthSessionDTO):
        await self.send_request(
            "actions/upload-auth-session", data=dto.dict(), method="POST"
        )

    async def get_interactions_selector(self, dto: GetElementsDTO) -> dict:
        res = await self.send_request(
            "actions/get-interaction-selector", data=dto.dict(), method="POST"
        )
        return res

    async def make_interaction(self, dto: MakeInteractionDTO) -> InteractionResponse:
        res = await self.send_request(
            "actions/make-interaction", data=dto.dict(), method="POST"
        )
        return InteractionResponse(status=res["status"], message=res["message"])

    async def scrape_page(self, dto: ScrapePageDTO) -> ScrapePageResponse:
        res = await self.send_request(
            "actions/scrape-page", data=dto.dict(), method="POST"
        )
        return ScrapePageResponse(
            status=res["status"],
            message=res["message"],
            return_data=res["return_data"],
            created_script=res.get("created_script", None),
            used_cache=res.get("used_cache", False),
        )

    async def ask_page(self, dto: AskPageDTO) -> AskPageResponse:
        res = await self.send_request(
            "actions/ask-page", data=dto.dict(), method="POST"
        )
        return AskPageResponse(
            description=res["description"], return_data=res["return_data"]
        )

    async def try_run_cached(
        self, dto: TryRunScriptDTO
    ) -> Optional[ScrapePageResponse]:
        res = await self.send_request(
            "actions/try-run-cached", data=dto.dict(), method="POST"
        )
        if res is None:
            return None

        loaded_value = res["return_data"]
        if loaded_value == None:
            return None

        return ScrapePageResponse(
            status=res["status"],
            message=res["message"],
            return_data=loaded_value,
            created_script=res.get("created_script", None),
            used_cache=res.get("used_cache", False),
        )

    async def create_session(self) -> str:
        """
        Creates a new browser session.

        Returns:
            str: The ID of the created session.
        """
        res = await self.send_request("browser/sessions", method="POST")
        return res

    async def browser_ws_uri(self, session_id: Union[str, None]) -> str:
        """
        Generates the WebSocket URI for the browser session.

        Args:
            session_id (str | None): The ID of the browser session.

        Returns:
            str: The WebSocket URI.
        """
        base_url = resolve_base_url()
        url = base_url.split("://", maxsplit=1)[1]
        url = f"ws://{url}/browser/ws"

        if session_id:
            url += f"?session_id={session_id}"

        return url

    async def get_download(self, session_id: str):
        res = await self.send_request(
            f"browser/sessions/{session_id}/download", method="GET"
        )
        return res
