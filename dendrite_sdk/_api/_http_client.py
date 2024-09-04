from typing import Any, Optional

import httpx
from loguru import logger


from dendrite_sdk._common.constants import DENDRITE_API_BASE_URL


class HTTPClient:
    def __init__(self, api_key: Optional[str] = None, session_id: Optional[str] = None):
        self.api_key = api_key
        self.session_id = session_id
        self.base_url = self.resolve_base_url()

    def resolve_base_url(self):
        return DENDRITE_API_BASE_URL

    async def send_request(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        method: str = "GET",
    ) -> httpx.Response:
        url = f"{self.base_url}/{endpoint}"

        headers = headers or {}
        headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.session_id:
            headers["X-Session-ID"] = self.session_id

        async with httpx.AsyncClient(timeout=300) as client:
            try:
                response = await client.request(
                    method, url, params=params, json=data, headers=headers
                )
                response.raise_for_status()
                # logger.debug(
                #     f"{method} to '{url}', that took: { time.time() - start_time }\n\nResponse: {dict_res}\n\n"
                # )
                return response
            except httpx.HTTPStatusError as http_err:
                logger.debug(
                    f"HTTP error occurred: {http_err.response.status_code}: {http_err.response.text}"
                )
                raise
            except httpx.ConnectError as connect_err:
                logger.error(
                    f"Connection error occurred: {connect_err}. {url} Server might be down"
                )
                raise
            except httpx.RequestError as req_err:
                # logger.debug(f"Request error occurred: {req_err}")
                raise
            except Exception as err:
                # logger.debug(f"An error occurred: {err}")
                raise
