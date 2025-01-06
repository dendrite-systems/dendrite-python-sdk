from ..protocol.page_protocol import DendritePageProtocol


class ScreenshotMixin(DendritePageProtocol):

    async def screenshot(self, full_page: bool = False) -> str:
        """
        Take a screenshot of the current page.

        Args:
            full_page (bool, optional): If True, captures the full page. If False, captures only the viewport. Defaults to False.

        Returns:
            str: A base64 encoded string of the screenshot in JPEG format.
        """
        page = await self._get_page()
        if full_page:
            return await page.screenshot_manager.take_full_page_screenshot()
        else:
            return await page.screenshot_manager.take_viewport_screenshot()
