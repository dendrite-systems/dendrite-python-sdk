import asyncio
from typing import Any, Optional
from dendrite_sdk.async_api._api.response.interaction_response import (
    InteractionResponse,
)
from dendrite_sdk.async_api._core.mixin.get_element import GetElementMixin
from dendrite_sdk.async_api._core.protocol.page_protocol import DendritePageProtocol
from dendrite_sdk._common._exceptions.dendrite_exception import DendriteException


class ClickMixin(GetElementMixin, DendritePageProtocol):

    async def click(
        self,
        prompt: str,
        expected_outcome: Optional[str] = None,
        use_cache: bool = True,
        timeout: int = 15000,
        force: bool = False,
        *args,
        **kwargs,
    ) -> InteractionResponse:
        """
        Clicks an element on the page based on the provided prompt.

        This method combines the functionality of get_element and click,
        allowing for a more concise way to interact with elements on the page.

        Args:
            prompt (str): The prompt describing the element to be clicked.
            expected_outcome (Optional[str]): The expected outcome of the click action.
            use_cache (bool, optional): Whether to use cached results for element retrieval. Defaults to True.
            timeout (int, optional): The timeout (in milliseconds) for the click operation. Defaults to 15000.
            force (bool, optional): Whether to force the click operation. Defaults to False.
            *args: Additional positional arguments for the click operation.
            **kwargs: Additional keyword arguments for the click operation.

        Returns:
            InteractionResponse: The response from the interaction.

        Raises:
            DendriteException: If no suitable element is found or if the click operation fails.
        """
        element = await self.get_element(
            prompt,
            use_cache=use_cache,
            timeout=timeout,
        )

        if not element:
            raise DendriteException(
                message=f"No element found with the prompt: {prompt}",
                screenshot_base64="",
            )

        return await element.click(
            expected_outcome=expected_outcome,
            timeout=timeout,
            force=force,
            *args,
            **kwargs,
        )
