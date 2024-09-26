import asyncio
import time
from typing import Dict, List, Literal, Optional, Union, overload

from loguru import logger

from dendrite_sdk.async_api._api.dto.get_elements_dto import GetElementsDTO
from dendrite_sdk.async_api._core.dendrite_element import AsyncElement
from dendrite_sdk.async_api._core.models.response import AsyncElementsResponse
from dendrite_sdk.async_api._core.protocol.page_protocol import DendritePageProtocol
from dendrite_sdk._common._exceptions.dendrite_exception import DendriteException


# The timeout interval between retries in milliseconds
TIMEOUT_INTERVAL = [150, 450, 1000]


class GetElementMixin(DendritePageProtocol):
    @overload
    async def get_elements(
        self,
        prompt_or_elements: str,
        use_cache: bool = True,
        timeout: int = 15000,
        context: str = "",
    ) -> List[AsyncElement]:
        """
        Retrieves a list of Dendrite elements based on a string prompt.

        Args:
            prompt_or_elements (str): The prompt describing the elements to be retrieved.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            timeout (int, optional): The total timeout (in milliseconds) until the last request is sent to the API. Defaults to 15000 (15 seconds).
            context (str, optional): Additional context for the retrieval. Defaults to an empty string.

        Returns:
            List[AsyncElement]: A list of Dendrite elements found on the page.
        """

    @overload
    async def get_elements(
        self,
        prompt_or_elements: Dict[str, str],
        use_cache: bool = True,
        timeout: int = 15000,
        context: str = "",
    ) -> AsyncElementsResponse:
        """
        Retrieves Dendrite elements based on a dictionary.

        Args:
            prompt_or_elements (Dict[str, str]): A dictionary where keys are field names and values are prompts describing the elements to be retrieved.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            timeout (int, optional): The total timeout (in milliseconds) until the last request is sent to the API. Defaults to 3000.
            context (str, optional): Additional context for the retrieval. Defaults to an empty string.

        Returns:
            AsyncElementsResponse: A response object containing the retrieved elements with attributes matching the keys in the dict.
        """

    async def get_elements(
        self,
        prompt_or_elements: Union[str, Dict[str, str]],
        use_cache: bool = True,
        timeout: int = 15000,
        context: str = "",
    ) -> Union[List[AsyncElement], AsyncElementsResponse]:
        """
        Retrieves Dendrite elements based on either a string prompt or a dictionary of prompts.

        This method determines the type of the input (string or dictionary) and retrieves the appropriate elements.
        If the input is a string, it fetches a list of elements. If the input is a dictionary, it fetches elements for each key-value pair.

        Args:
            prompt_or_elements (Union[str, Dict[str, str]]): The prompt or dictionary of prompts for element retrieval.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            timeout (int, optional): The total timeout (in milliseconds) until the last request is sent to the API. Defaults to 3000.
            context (str, optional): Additional context for the retrieval. Defaults to an empty string.

        Returns:
            Union[List[AsyncElement], AsyncElementsResponse]: A list of elements or a response object containing the retrieved elements.

        Raises:
            ValueError: If the input is neither a string nor a dictionary.
        """

        return await self._get_element(
            prompt_or_elements,
            only_one=False,
            use_cache=use_cache,
            timeout=timeout,
        )

        raise ValueError("Prompt must be either a string prompt or a dictionary")

    async def get_element(
        self,
        prompt: str,
        use_cache=True,
        timeout=15000,
    ) -> Optional[AsyncElement]:
        """
        Retrieves a single Dendrite element based on the provided prompt.

        Args:
            prompt (str): The prompt describing the element to be retrieved.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            timeout (int, optional): The total timeout (in milliseconds) until the last request is sent to the API. Defaults to 15000 (15 seconds).

        Returns:
            AsyncElement: The retrieved element.
        """
        return await self._get_element(
            prompt,
            only_one=True,
            use_cache=use_cache,
            timeout=timeout,
        )

    @overload
    async def _get_element(
        self,
        prompt_or_elements: str,
        only_one: Literal[True],
        use_cache: bool,
        timeout,
    ) -> Optional[AsyncElement]:
        """
        Retrieves a single Dendrite element based on the provided prompt.

        Args:
            prompt (Union[str, Dict[str, str]]): The prompt describing the element to be retrieved.
            only_one (Literal[True]): Indicates that only one element should be retrieved.
            use_cache (bool): Whether to use cached results.
            timeout: The total timeout (in milliseconds) until the last request is sent to the API.

        Returns:
            AsyncElement: The retrieved element.
        """

    @overload
    async def _get_element(
        self,
        prompt_or_elements: Union[str, Dict[str, str]],
        only_one: Literal[False],
        use_cache: bool,
        timeout,
    ) -> Union[List[AsyncElement], AsyncElementsResponse]:
        """
        Retrieves a list of Dendrite elements based on the provided prompt.

        Args:
            prompt (str): The prompt describing the elements to be retrieved.
            only_one (Literal[False]): Indicates that multiple elements should be retrieved.
            use_cache (bool): Whether to use cached results.
            timeout: The total timeout (in milliseconds) until the last request is sent to the API.

        Returns:
            List[AsyncElement]: A list of retrieved elements.
        """

    async def _get_element(
        self,
        prompt_or_elements: Union[str, Dict[str, str]],
        only_one: bool,
        use_cache: bool,
        timeout: float,
    ) -> Union[
        Optional[AsyncElement],
        List[AsyncElement],
        AsyncElementsResponse,
    ]:
        """
        Retrieves Dendrite elements based on the provided prompt, either a single element or a list of elements.

        This method sends a request with the prompt and retrieves the elements based on the `only_one` flag.

        Args:
            prompt_or_elements (Union[str, Dict[str, str]]): The prompt or dictionary of prompts for element retrieval.
            only_one (bool): Whether to retrieve only one element or a list of elements.
            use_cache (bool): Whether to use cached results.
            timeout (float): The total timeout (in milliseconds) until the last request is sent to the API.

        Returns:
            Union[AsyncElement, List[AsyncElement], AsyncElementsResponse]: The retrieved element, list of elements, or response object.
        """

        api_config = self._get_dendrite_browser().api_config
        start_time = time.time()
        attempt_start = start_time
        attempt = -1
        force_not_use_cache = False
        while True:
            attempt += 1
            current_timeout = (
                TIMEOUT_INTERVAL[attempt]
                if len(TIMEOUT_INTERVAL) > attempt
                else current_timeout * 1.75  # Default to 1 second if not specified
            )

            elapsed_time = time.time() - start_time
            remaining_time = timeout * 0.001 - elapsed_time

            if remaining_time <= 8 or attempt > 2:
                logger.debug(
                    f"Forcing cache bypass: remaining_time={remaining_time}, attempt={attempt}"
                )
                force_not_use_cache = True

            if remaining_time <= 0:
                logger.warning(
                    f"Timeout reached for '{prompt_or_elements}' after {attempt + 1} attempts"
                )
                break

            prev_attempt_time = time.time() - attempt_start

            sleep_time = min(
                max(current_timeout * 0.001 - prev_attempt_time, 0), remaining_time
            )
            logger.debug(f"Waiting for {sleep_time} seconds before retrying")
            await asyncio.sleep(sleep_time)
            attempt_start = time.time()

            logger.info(
                f"Getting element for '{prompt_or_elements}' | Attempt {attempt + 1}"
            )

            page = await self._get_page()
            page_information = await page.get_page_information()

            dto = GetElementsDTO(
                page_information=page_information,
                prompt=prompt_or_elements,
                api_config=api_config,
                use_cache=use_cache and not force_not_use_cache,
                only_one=only_one,
            )
            res = await self._get_browser_api_client().get_interactions_selector(dto)

            logger.debug(
                f"Got selectors: {res} in {time.time() - attempt_start} seconds"
            )

            if isinstance(res.selectors, dict):
                result = {}
                for key, selectors in res.selectors.items():
                    for selector in reversed(selectors):
                        page = await self._get_page()
                        dendrite_elements = await page._get_all_elements_from_selector(
                            selector
                        )
                        if len(dendrite_elements) > 0:
                            logger.info(f"Got working selector for '{key}': {selector}")
                            result[key] = dendrite_elements[0]
                            break
                    else:
                        logger.warning(
                            f"No elements found for '{key}' on attempt {attempt + 1}"
                        )
                return AsyncElementsResponse(result)
            elif isinstance(res.selectors, list):
                for selector in reversed(res.selectors):
                    page = await self._get_page()
                    dendrite_elements = await page._get_all_elements_from_selector(
                        selector
                    )
                    if len(dendrite_elements) > 0:
                        logger.info(f"Got working selector: {selector}")
                        return dendrite_elements[0] if only_one else dendrite_elements
                    else:
                        logger.warning(
                            f"No elements found for selector: {selector} on attempt {attempt + 1}"
                        )

            logger.warning(
                f"All selectors failed for '{prompt_or_elements}' on attempt {attempt + 1}"
            )

        logger.error(
            f"Failed to get elements for '{prompt_or_elements}' after {attempt + 1} attempts"
        )
        return None
