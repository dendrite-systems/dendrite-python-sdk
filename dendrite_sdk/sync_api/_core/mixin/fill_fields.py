import time
from typing import Any, Dict, Optional
from dendrite_sdk.sync_api._api.response.interaction_response import InteractionResponse
from dendrite_sdk.sync_api._core.mixin.get_element import GetElementMixin
from dendrite_sdk.sync_api._core.protocol.page_protocol import DendritePageProtocol
from dendrite_sdk._common._exceptions.dendrite_exception import DendriteException


class FillFieldsMixin(GetElementMixin, DendritePageProtocol):

    def fill_fields(self, fields: Dict[str, Any]):
        """
        Fills multiple fields on the page with the provided values.

        This method iterates through the given dictionary of fields and their corresponding values,
        making a separate fill request for each key-value pair.

        Args:
            fields (Dict[str, Any]): A dictionary where each key is a field identifier (e.g., a prompt or selector)
                                     and each value is the content to fill in that field.

        Returns:
            None

        Note:
            This method will make multiple fill requests, one for each key in the 'fields' dictionary.
        """
        for field, value in fields.items():
            prompt = f"I'll be filling in several values from a object with these keys: {fields.keys()} in this page. Get the field best described as '{field}'. I want to fill it with a '{type(value)}' type value."
            self.fill(prompt, value)
            time.sleep(0.5)

    def fill(
        self,
        prompt: str,
        value: str,
        expected_outcome: Optional[str] = None,
        use_cache: bool = True,
        timeout: int = 15000,
        *args,
        kwargs={},
    ) -> InteractionResponse:
        """
        Fills an element on the page with the provided value based on the given prompt.

        This method combines the functionality of get_element and fill,
        allowing for a more concise way to interact with elements on the page.

        Args:
            prompt (str): The prompt describing the element to be filled.
            value (str): The value to fill the element with.
            expected_outcome (Optional[str]): The expected outcome of the fill action.
            use_cache (bool, optional): Whether to use cached results for element retrieval. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts for element retrieval. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) for the fill operation. Defaults to 15000.
            *args: Additional positional arguments for the fill operation.
            kwargs: Additional keyword arguments for the fill operation.

        Returns:
            InteractionResponse: The response from the interaction.

        Raises:
            DendriteException: If no suitable element is found or if the fill operation fails.
        """
        element = self.get_element(prompt, use_cache=use_cache, timeout=timeout)
        if not element:
            raise DendriteException(
                message=f"No element found with the prompt: {prompt}",
                screenshot_base64="",
            )
        return element.fill(
            value, *args, expected_outcome=expected_outcome, timeout=timeout, **kwargs
        )
