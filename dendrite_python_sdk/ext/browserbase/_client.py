import asyncio
import os
from pathlib import Path
import time
from typing import Union
import httpx
from loguru import logger


async def create_session() -> str:
    logger.debug("Creating session")
    """
    Creates a session using the BrowserBase API.

    Returns:
        str: The ID of the created session.
    """
    url = "https://www.browserbase.com/v1/sessions"
    headers = {
        "Content-Type": "application/json",
        "x-bb-api-key": os.environ["BROWSERBASE_API_KEY"],
    }
    json = {
        "projectId": os.environ["BROWSERBASE_PROJECT_ID"],
        "keepAlive": False,
    }
    response = httpx.post(url, json=json, headers=headers)
    return response.json()["id"]


async def stop_session(session_id: str):
    url = f"https://www.browserbase.com/v1/sessions/{session_id}"

    headers = {
        "Content-Type": "application/json",
        "x-bb-api-key": os.environ["BROWSERBASE_API_KEY"],
    }
    json = {
        "projectId": os.environ["BROWSERBASE_PROJECT_ID"],
        "status": "REQUEST_RELEASE",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=json, headers=headers)

    return response.json()


async def save_downloads_on_disk(
    session_id: str, path: Union[str, Path], retry_for_seconds: int
):
    url = f"https://www.browserbase.com/v1/sessions/{session_id}/downloads"
    headers = {
        "x-bb-api-key": os.environ["BROWSERBASE_API_KEY"],
    }

    path = Path(path)

    # Determine the correct file path
    if path.is_dir():
        file_path = path / "downloads.zip"
    else:
        # Ensure the file has a .zip extension
        if path.suffix != ".zip":
            raise ValueError("The file name provided must have a .zip extension.")
        file_path = path

    async with httpx.AsyncClient() as session:
        timeout = time.time() + retry_for_seconds
        while time.time() < timeout:
            try:
                response = await session.get(url, headers=headers)
                if response.status_code == 200:
                    array_buffer = response.read()
                    if len(array_buffer) > 0:
                        with open(file_path, "wb") as f:
                            f.write(array_buffer)
                        return
            except Exception as e:
                print(f"Error fetching downloads: {e}")
            await asyncio.sleep(2)
        print("Failed to download files within the time limit.")
