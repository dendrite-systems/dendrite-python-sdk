import httpx
from dendrite_python_sdk.dto.MakeInteractionDTO import (
    MakeInteractionDTO,
)
from dendrite_python_sdk.dto.GetInteractionDTO import GetInteractionDTO
from dendrite_python_sdk.responses.InteractionResponse import InteractionResponse


async def send_request(
    endpoint,
    params=None,
    data: dict | None = None,
    headers=None,
    method="GET",
):
    base_url = "http://localhost:8000/api/v1"  # "https://dendrite.se/api/v1"
    url = f"{base_url}/{endpoint}"
    headers = headers or {}
    headers["Content-Type"] = "application/json"

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
