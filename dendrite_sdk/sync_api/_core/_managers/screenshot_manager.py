import time
import base64
import os
from typing import Tuple
from uuid import uuid4
from dendrite_sdk.sync_api._core._type_spec import PlaywrightPage


class ScreenshotManager:

    def __init__(self, page: PlaywrightPage) -> None:
        self.screenshot_before: str = ""
        self.screenshot_after: str = ""
        self.page = page

    def take_full_page_screenshot(self) -> str:
        time.sleep(0.5)
        image_data = self.page.screenshot(type="jpeg", full_page=True, timeout=30000)
        if image_data is None:
            return ""
        return base64.b64encode(image_data).decode("utf-8")

    def take_viewport_screenshot(self) -> str:
        image_data = self.page.screenshot(type="jpeg", timeout=30000)
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
