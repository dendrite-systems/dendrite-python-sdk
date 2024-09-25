import time
from pathlib import Path
import time
from typing import Optional, Union
import httpx
from loguru import logger


class BrowserbaseClient:

    def __init__(self, api_key: str, project_id: str) -> None:
        self.api_key = api_key
        self.project_id = project_id

    def create_session(self) -> str:
        logger.debug("Creating session")
        "\n        Creates a session using the Browserbase API.\n\n        Returns:\n            str: The ID of the created session.\n        "
        url = "https://www.browserbase.com/v1/sessions"
        headers = {"Content-Type": "application/json", "x-bb-api-key": self.api_key}
        json = {"projectId": self.project_id, "keepAlive": False}
        response = httpx.post(url, json=json, headers=headers)
        return response.json()["id"]

    def stop_session(self, session_id: str):
        url = f"https://www.browserbase.com/v1/sessions/{session_id}"
        headers = {"Content-Type": "application/json", "x-bb-api-key": self.api_key}
        json = {"projectId": self.project_id, "status": "REQUEST_RELEASE"}
        with httpx.Client() as client:
            response = client.post(url, json=json, headers=headers)
        return response.json()

    def connect_url(self, enable_proxy: bool, session_id: Optional[str] = None) -> str:
        url = f"wss://connect.browserbase.com?apiKey={self.api_key}"
        if session_id:
            url += f"&sessionId={session_id}"
        if enable_proxy:
            url += "&enableProxy=true"
        return url

    def save_downloads_on_disk(
        self, session_id: str, path: Union[str, Path], retry_for_seconds: float
    ):
        url = f"https://www.browserbase.com/v1/sessions/{session_id}/downloads"
        headers = {"x-bb-api-key": self.api_key}
        file_path = Path(path)
        with httpx.Client() as session:
            timeout = time.time() + retry_for_seconds
            while time.time() < timeout:
                try:
                    response = session.get(url, headers=headers)
                    if response.status_code == 200:
                        array_buffer = response.read()
                        if len(array_buffer) > 0:
                            with open(file_path, "wb") as f:
                                f.write(array_buffer)
                            return
                except Exception as e:
                    logger.debug(f"Error fetching downloads: {e}")
                time.sleep(2)
            logger.debug("Failed to download files within the time limit.")