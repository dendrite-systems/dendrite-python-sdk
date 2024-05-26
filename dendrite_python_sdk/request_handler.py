import json
import sys
import httpx
from dendrite_python_sdk.dto.MakeInteractionDTO import (
    MakeInteractionDTO,
)
from dendrite_python_sdk.dto.GetInteractionDTO import GetInteractionDTO
from dendrite_python_sdk.dto.ScrapePageDTO import ScrapePageDTO
from dendrite_python_sdk.dto.GoogleSearchDTO import GoogleSearchDTO
from dendrite_python_sdk.responses.GoogleSearchResponse import GoogleSearchResponse
from dendrite_python_sdk.responses.InteractionResponse import InteractionResponse
from dendrite_python_sdk.responses.ScrapePageResponse import ScrapePageResponse
from dendrite_python_sdk.responses.ScrapePageResponse import ScrapePageResponse

config = {"dendrite_api_key": ""}
dev_mode = True if "--dev" in sys.argv else False


async def send_request(
    endpoint,
    params=None,
    data: dict | None = None,
    headers=None,
    method="GET",
):
    base_url = (
        "http://localhost:8000/api/v1"
        if dev_mode
        else "https://dendrite-server.azurewebsites.net/api/v1"
    )
    url = f"{base_url}/{endpoint}"
    headers = headers or {}
    headers["Content-Type"] = "application/json"
    if config["dendrite_api_key"] != "":
        headers["Authorization"] = f"Bearer {config['dendrite_api_key']}"

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.request(
            method, url, params=params, json=data, headers=headers
        )
        response.raise_for_status()
        return response.json()


async def get_interaction(dto: GetInteractionDTO) -> dict:
    res = await send_request("actions/get-interaction", data=dto.dict(), method="POST")
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


async def google_search_request(dto: GoogleSearchDTO) -> GoogleSearchResponse:
    res = await send_request("actions/google-search", data=dto.dict(), method="POST")
    return GoogleSearchResponse(results=res["results"])
