import asyncio
import time


from dendrite_sdk.async_api._core.mixin.ask import AskMixin
from dendrite_sdk.async_api._core.protocol.page_protocol import DendritePageProtocol
from dendrite_sdk._common._exceptions.dendrite_exception import PageConditionNotMet
from dendrite_sdk._common._exceptions.dendrite_exception import DendriteException

from loguru import logger


class WaitForMixin(AskMixin, DendritePageProtocol):

    async def wait_for(
        self,
        prompt: str,
        timeout: float = 30000,
    ):
        """
        Waits for the condition specified in the prompt to become true by periodically checking the page content.

        This method attempts to retrieve the page information and evaluate whether the specified
        condition (provided in the prompt) is met. It continues to retry until the total elapsed time
        exceeds the specified timeout.

        Args:
            prompt (str): The prompt to determine the condition to wait for on the page.
            timeout (float, optional): The maximum time (in milliseconds) to wait for the condition. Defaults to 15000.

        Returns:
            Any: The result of the condition evaluation if successful.

        Raises:
            PageConditionNotMet: If the condition is not met within the specified timeout.
        """

        start_time = time.time()
        await asyncio.sleep(
            0.2
        )  # HACK: Wait for page to load slightly when running first time

        while True:
            elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            if elapsed_time >= timeout:
                break

            page = await self._get_page()
            page_information = await page.get_page_information()
            prompt_with_instruction = f"Prompt: '{prompt}'\n\nReturn a boolean that determines if the requested information or thing is available on the page."

            try:
                res = await self.ask(prompt_with_instruction, bool)
                if res:
                    return res
            except DendriteException as e:
                logger.debug(f"Attempt failed: {e.message}")

            # Wait for a short interval before the next attempt
            await asyncio.sleep(0.5)

        page = await self._get_page()
        page_information = await page.get_page_information()
        raise PageConditionNotMet(
            message=f"Failed to wait for the requested condition within the {timeout}ms timeout.",
            screenshot_base64=page_information.screenshot_base64,
        )
