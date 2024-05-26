import asyncio
import base64
from typing import Tuple
from playwright.async_api import Page


class ScreenshotManager:
    def __init__(self) -> None:
        self.screenshot_before: str = ""
        self.screenshot_after: str = ""

    async def take_full_page_screenshot(self, page: Page) -> str:
        # await page.screenshot(path="screenshot.png", full_page=True)
        image_data = await page.screenshot(type="jpeg", full_page=True, timeout=20000)
        print("image_data: ", image_data)

        if image_data == None:
            return ""

        return base64.b64encode(image_data).decode()

    async def take_element_screenshot(self, page: Page, selector: str) -> str:
        element = page.locator(selector)
        image_data = await element.screenshot(type="jpeg", timeout=20000)

        if image_data == None:
            return ""

        return base64.b64encode(image_data).decode()

    async def take_viewport_screenshot(self, page: Page) -> str:
        image_data = await page.screenshot(type="jpeg", timeout=10000)

        if image_data == None:
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
