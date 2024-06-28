import asyncio
import base64
import os
from typing import Optional, Tuple
from uuid import uuid4
from playwright.async_api import Page


class ScreenshotManager:
    def __init__(self) -> None:
        self.screenshot_before: str = ""
        self.screenshot_after: str = ""

    async def take_full_page_screenshot(self, page: Page) -> str:
        image_data = await page.screenshot(type="jpeg", full_page=True, timeout=30000)
        print(f"Screenshot size: {len(image_data)} bytes")
        self.store_screenshot("full_test", image_data)
        if image_data == None:
            return ""

        return base64.b64encode(image_data).decode("utf-8")

    async def take_element_screenshot(self, page: Page, selector: str) -> str:
        element = page.locator(selector)
        image_data = await element.screenshot(type="jpeg", timeout=20000)

        if image_data == None:
            return ""

        return base64.b64encode(image_data).decode()

    async def take_viewport_screenshot(self, page: Page) -> str:
        image_data = await page.screenshot(type="jpeg", timeout=30000)

        if image_data == None:
            return ""

        self.store_screenshot("test", image_data)

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
        print(f"Screenshot saved to {filepath}")
        return filepath
