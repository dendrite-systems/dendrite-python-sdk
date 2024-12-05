import time
import time
from loguru import logger
from dendrite.browser._common._exceptions.dendrite_exception import (
    DendriteException,
    PageConditionNotMet,
)
from ..mixin.ask import AskMixin
from ..protocol.page_protocol import DendritePageProtocol


class WaitForMixin(AskMixin, DendritePageProtocol):

    def wait_for(self, prompt: str, timeout: float = 30000):
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
        time.sleep(0.2)
        while True:
            elapsed_time = (time.time() - start_time) * 1000
            if elapsed_time >= timeout:
                break
            page = self._get_page()
            page_information = page.get_page_information()
            prompt_with_instruction = f"Prompt: '{prompt}'\n\nReturn a boolean that determines if the requested information or thing is available on the page. {round(page_information.time_since_frame_navigated, 2)} seconds have passed since the page first loaded."
            try:
                res = self.ask(prompt_with_instruction, bool)
                if res:
                    return res
            except DendriteException as e:
                logger.debug(f"Attempt failed: {e.message}")
            time.sleep(0.5)
        page = self._get_page()
        page_information = page.get_page_information()
        raise PageConditionNotMet(
            message=f"Failed to wait for the requested condition within the {timeout}ms timeout.",
            screenshot_base64=page_information.screenshot_base64,
        )
