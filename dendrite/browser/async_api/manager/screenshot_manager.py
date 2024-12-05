import base64
import os
from uuid import uuid4

from ..types import PlaywrightPage


class ScreenshotManager:
    def __init__(self, page: PlaywrightPage) -> None:
        self.screenshot_before: str = ""
        self.screenshot_after: str = ""
        self.page = page

    async def take_full_page_screenshot(self) -> str:
        try:
            # Check the page height
            scroll_height = await self.page.evaluate(
                """
                () => {
                    const body = document.body;
                    if (!body) {
                        return 0;  // Return 0 if body is null
                    }
                    return body.scrollHeight || 0;
                }
                """
            )

            if scroll_height > 30000:
                print(
                    f"Page height ({scroll_height}px) exceeds 30000px. Taking viewport screenshot instead."
                )
                return await self.take_viewport_screenshot()

            # Attempt to take a full-page screenshot
            image_data = await self.page.screenshot(
                type="jpeg", full_page=True, timeout=10000
            )
        except Exception as e:  # Catch any exception, including timeout
            print(
                f"Full-page screenshot failed: {e}. Falling back to viewport screenshot."
            )
            # Fall back to viewport screenshot
            return await self.take_viewport_screenshot()

        if image_data is None:
            return ""

        return base64.b64encode(image_data).decode("utf-8")

    async def take_viewport_screenshot(self) -> str:
        image_data = await self.page.screenshot(type="jpeg", timeout=10000)

        if image_data is None:
            return ""

        reduced_base64 = base64.b64encode(image_data).decode("utf-8")

        return reduced_base64

    def store_screenshot(self, name, image_data):
        if not name:
            name = str(uuid4())
        filepath = os.path.join("test", f"{name}.jpeg")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "wb") as file:
            file.write(image_data)
        return filepath
