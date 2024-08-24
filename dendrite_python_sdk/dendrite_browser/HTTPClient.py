import sys
import time
import httpx
from typing import Any, Optional


dev_mode = True if "--dev" in sys.argv else False


class HTTPClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = self.resolve_base_url()

    def resolve_base_url(self):
        return (
            "http://localhost:8000/api/v1"
            if dev_mode
            else "https://dendrite-server.azurewebsites.net/api/v1"
        )

    async def send_request(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        method: str = "GET",
    ) -> Any:
        url = f"{self.base_url}/{endpoint}"

        headers = headers or {}
        headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=300) as client:
            try:
                start_time = time.time()
                response = await client.request(
                    method, url, params=params, json=data, headers=headers
                )
                response.raise_for_status()
                print(f"{method} to '{url}', that took: { time.time() - start_time }")

                return response.json()
            except httpx.HTTPStatusError as http_err:
                detail = http_err.response.json()
                print(
                    f"HTTP error occurred: {http_err.response.status_code}: {detail['detail']}"
                )
                raise
            except httpx.RequestError as req_err:
                print(f"Request error occurred: {req_err}")
                raise
            except Exception as err:
                print(f"An error occurred: {err}")
                raise
