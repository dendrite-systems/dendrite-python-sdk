import json
import sys
from typing import Optional, Union
import httpx
from dendrite_python_sdk.dto.MakeInteractionDTO import MakeInteractionDTO
from dendrite_python_sdk.dto.GetInteractionDTO import GetInteractionDTO
from dendrite_python_sdk.dto.ScrapePageDTO import ScrapePageDTO
from dendrite_python_sdk.dto.GoogleSearchDTO import GoogleSearchDTO
from dendrite_python_sdk.dto.TryRunScriptDTO import TryRunScriptDTO
from dendrite_python_sdk.responses.GoogleSearchResponse import GoogleSearchResponse
from dendrite_python_sdk.responses.InteractionResponse import InteractionResponse
from dendrite_python_sdk.responses.ScrapePageResponse import ScrapePageResponse

config = {"dendrite_api_key": ""}
dev_mode = True if "--dev" in sys.argv else False


async def send_request(
    endpoint, params=None, data: Optional[dict] = None, headers=None, method="GET"
):
    base_url = resolve_base_url()
    url = f"{base_url}/{endpoint}"
    headers = headers or {}
    headers["Content-Type"] = "application/json"
    if config["dendrite_api_key"] != "":
        headers["Authorization"] = f"Bearer {config['dendrite_api_key']}"

    async with httpx.AsyncClient(timeout=300) as client:
        try:
            response = await client.request(
                method, url, params=params, json=data, headers=headers
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as http_err:
            detail = http_err.response.json()
            print(
                f"HTTP error occurred: {http_err.response.status_code}: {detail['detail']}"
            )
            raise http_err
        except httpx.RequestError as req_err:
            print(f"Request error occurred: {req_err}")
            raise req_err
        except Exception as err:
            print(f"An error occurred: {err}")
            raise err


def resolve_base_url():
    base_url = (
        "http://localhost:8000/api/v1"
        if dev_mode
        else "https://dendrite-server.azurewebsites.net/api/v1"
    )

    return base_url


async def get_interaction(dto: GetInteractionDTO) -> dict:
    res = await send_request("actions/get-interaction", data=dto.dict(), method="POST")
    return res


async def get_interactions(dto: GetInteractionDTO) -> dict:
    res = await send_request("actions/get-interactions", data=dto.dict(), method="POST")
    return res


async def get_interactions_selector(dto: ScrapePageDTO) -> dict:
    res = await send_request(
        "actions/get-interaction-selector", data=dto.dict(), method="POST"
    )
    return res


async def make_interaction(dto: MakeInteractionDTO) -> InteractionResponse:
    res = await send_request("actions/make-interaction", data=dto.dict(), method="POST")
    return InteractionResponse(status=res["status"], message=res["message"])


async def scrape_page(dto: ScrapePageDTO) -> ScrapePageResponse:
    res = await send_request("actions/scrape-page", data=dto.dict(), method="POST")
    return ScrapePageResponse(
        status=res["status"],
        message=res["message"],
        json_data=json.loads(res["json_data"]),
    )

async def try_run_cached(dto: TryRunScriptDTO) -> Optional[ScrapePageResponse]:
    res = await send_request("actions/try-run-cached", data=dto.dict(), method="POST")
    if res is None:
        return None
    
    return ScrapePageResponse(
        status=res["status"],
        message=res["message"],
        json_data=json.loads(res["json_data"]),
    )


async def google_search_request(dto: GoogleSearchDTO) -> GoogleSearchResponse:
    res = await send_request("actions/google-search", data=dto.dict(), method="POST")
    return GoogleSearchResponse(results=res["results"])


async def create_session() -> str:
    """
    Creates a new browser session.

    Returns:
        str: The ID of the created session.
    """
    res = await send_request("browser/sessions", method="POST")
    return res


async def browser_ws_uri(session_id: Union[str, None]) -> str:
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


async def get_download(session_id: str):
    res = await send_request(f"browser/sessions/{session_id}/download", method="GET")
    return res
