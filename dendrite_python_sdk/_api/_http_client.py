import json
import time
from typing import Any, Optional

import httpx
from loguru import logger


from dendrite_python_sdk._common.constants import DENDRITE_API_BASE_URL


class HTTPClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = self.resolve_base_url()

    def resolve_base_url(self):
        return "http://localhost:8000/api/v1"
        # return DENDRITE_API_BASE_URL
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
                dict_res = response.json()
                # logger.debug(
                #     f"{method} to '{url}', that took: { time.time() - start_time }\n\nResponse: {dict_res}\n\n"
                # )
                return dict_res
            except httpx.HTTPStatusError as http_err:
                detail = http_err.response.json()
                with open("error.json", "w") as f:
                    f.write(json.dumps(http_err.response.json(),indent=2))
                logger.debug(
                    f"HTTP error occurred: {http_err.response.status_code}: {http_err.response.text}"
                )
                raise
            except httpx.RequestError as req_err:
                # logger.debug(f"Request error occurred: {req_err}")
                raise
            except Exception as err:
                # logger.debug(f"An error occurred: {err}")
                raise
