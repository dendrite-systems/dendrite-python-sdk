import os
from typing import Optional
import httpx
from loguru import logger
from dendrite.sync_api._core.models.api_config import APIConfig


class HTTPClient:

    def __init__(self, api_config: APIConfig, session_id: Optional[str] = None):
        self.api_key = api_config.dendrite_api_key
        self.session_id = session_id
        self.base_url = self.resolve_base_url()

    def resolve_base_url(self):
        base_url = (
            "http://localhost:8000/api/v1"
            if os.environ.get("DENDRITE_DEV")
            else "https://dendrite-server.azurewebsites.net/api/v1"
        )
        return base_url

    def send_request(
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
        with httpx.Client(timeout=300) as client:
            try:
                response = client.request(
                    method, url, params=params, json=data, headers=headers
                )
                response.raise_for_status()
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
                raise
            except Exception as err:
                raise
