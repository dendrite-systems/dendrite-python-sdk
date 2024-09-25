import asyncio
import base64
import os
from typing import Tuple
from uuid import uuid4
from playwright.async_api import Page


class ScreenshotManager:
    def __init__(self) -> None:
        self.screenshot_before: str = ""
        self.screenshot_after: str = ""

    async def take_full_page_screenshot(self, page: Page) -> str:
        image_data = await page.screenshot(type="jpeg", full_page=True, timeout=30000)
        if image_data is None:
            return ""

        return base64.b64encode(image_data).decode("utf-8")

    async def take_viewport_screenshot(self, page: Page) -> str:
        image_data = await page.screenshot(type="jpeg", timeout=30000)

        if image_data is None:
            return ""

        reduced_base64 = base64.b64encode(image_data).decode("utf-8")

        return reduced_base64

    async def start_recording_diff(self, page: Page):
        self.screenshot_before = await self.take_viewport_screenshot(page)

    async def get_diff_images(
        self,
        page: Page,
        wait_time=1,
    ) -> Tuple[str, str]:
        await asyncio.sleep(wait_time)
        self.screenshot_after = await self.take_viewport_screenshot(page)
        return self.screenshot_before, self.screenshot_after

    def store_screenshot(self, name, image_data):
        if not name:
            name = str(uuid4())
        filepath = os.path.join("test", f"{name}.jpeg")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "wb") as file:
            file.write(image_data)
        return filepath
