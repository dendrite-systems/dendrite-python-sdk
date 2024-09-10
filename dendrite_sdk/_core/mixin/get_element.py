import asyncio
from typing import Dict, List, Literal, Optional, Union, overload

from loguru import logger

from dendrite_sdk._api.dto.get_elements_dto import GetElementsDTO
from dendrite_sdk._core.dendrite_element import DendriteElement
from dendrite_sdk._core.models.response import DendriteElementsResponse
from dendrite_sdk._core.protocol.page_protocol import DendritePageProtocol
from dendrite_sdk._exceptions.dendrite_exception import DendriteException


class GetElementMixin(DendritePageProtocol):
    @overload
    async def get_elements(
        self,
        prompt_or_elements: str,
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 3000,
        context: str = "",
    ) -> List[DendriteElement]:
        """
        Retrieves a list of Dendrite elements based on a string prompt.

        Args:
            prompt_or_elements (str): The prompt describing the elements to be retrieved.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) between retries. Defaults to 3.
            context (str, optional): Additional context for the retrieval. Defaults to an empty string.

        Returns:
            List[DendriteElement]: A list of Dendrite elements found on the page.
        """

    @overload
    async def get_elements(
        self,
        prompt_or_elements: Dict[str, str],
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 3000,
        context: str = "",
    ) -> DendriteElementsResponse:
        """
        Retrieves Dendrite elements based on a dictionary.

        Args:
            prompt_or_elements (Dict[str, str]): A dictionary where keys are field names and values are prompts describing the elements to be retrieved.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) between retries. Defaults to 3.
            context (str, optional): Additional context for the retrieval. Defaults to an empty string.

        Returns:
            DendriteElementsResponse: A response object containing the retrieved elements with attributes matching the keys in the dict.
        """

    async def get_elements(
        self,
        prompt_or_elements: Union[str, Dict[str, str]],
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 3000,
        context: str = "",
    ) -> Union[List[DendriteElement], DendriteElementsResponse]:
        """
        Retrieves Dendrite elements based on either a string prompt or a dictionary of prompts.

        This method determines the type of the input (string or dictionary) and retrieves the appropriate elements.
        If the input is a string, it fetches a list of elements. If the input is a dictionary, it fetches elements for each key-value pair.

        Args:
            prompt_or_elements (Union[str, Dict[str, str]]): The prompt or dictionary of prompts for element retrieval.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) between retries. Defaults to 3.
            context (str, optional): Additional context for the retrieval. Defaults to an empty string.

        Returns:
            Union[List[DendriteElement], DendriteElementsResponse]: A list of elements or a response object containing the retrieved elements.

        Raises:
            ValueError: If the input is neither a string nor a dictionary.
        """

        if isinstance(prompt_or_elements, str):
            return await self._get_element(
                prompt_or_elements,
                only_one=False,
                use_cache=use_cache,
                max_retries=max_retries,
                timeout=timeout,
            )
        if isinstance(prompt_or_elements, dict):
            return await self.get_elements_from_dict(
                prompt_or_elements, context, use_cache, max_retries, timeout
            )

        raise ValueError("Prompt must be either a string prompt or a dictionary")

    async def get_elements_from_dict(
        self,
        prompt_dict: Dict[str, str],
        context: str,
        use_cache: bool,
        max_retries: int,
        timeout: int,
    ):
        """
        Retrieves Dendrite elements based on a dictionary of prompts, each associated with a context.

        This method sends a request for each prompt in the dictionary, adding context to each prompt, and retrieves the corresponding elements.

        Args:
            prompt_dict (Dict[str, str]): A dictionary where keys are field names and values are prompts describing the elements to be retrieved.
            context (str): Additional context to be added to each prompt.
            use_cache (bool): Whether to use cached results.
            max_retries (int): The maximum number of retry attempts.
            timeout (int): The timeout (in milliseconds) between retries.

        Returns:
            DendriteElementsResponse: A response object containing the retrieved elements mapped to their corresponding field names.
        """
        tasks = []
        for field_name, prompt in prompt_dict.items():
            full_prompt = prompt
            if context != "":
                full_prompt += f"\n\nHere is some extra context: {context}"
            task = self._get_element(
                full_prompt,
                only_one=True,
                use_cache=use_cache,
                max_retries=max_retries,
                timeout=timeout,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        elements_dict: Dict[str, DendriteElement] = {}
        for element, field_name in zip(results, prompt_dict.keys()):
            elements_dict[field_name] = element
        return DendriteElementsResponse(elements_dict)

    async def get_element(
        self,
        prompt: str,
        use_cache=True,
        max_retries=2,
        timeout=3000,
    ) -> Optional[DendriteElement]:
        """
        Retrieves a single Dendrite element based on the provided prompt.

        Args:
            prompt (str): The prompt describing the element to be retrieved.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            max_retries (int, optional): The maximum number of retry attempts. Defaults to 3.
            timeout (int, optional): The timeout (in milliseconds) between retries. Defaults to 3.

        Returns:
            DendriteElement: The retrieved element.
        """
        return await self._get_element(
            prompt,
            only_one=True,
            use_cache=use_cache,
            max_retries=max_retries,
            timeout=timeout,
        )

    @overload
    async def _get_element(
        self,
        prompt: str,
        only_one: Literal[True],
        use_cache: bool,
        max_retries,
        timeout,
    ) -> Optional[DendriteElement]:
        """
        Retrieves a single Dendrite element based on the provided prompt.

        Args:
            prompt (str): The prompt describing the element to be retrieved.
            only_one (Literal[True]): Indicates that only one element should be retrieved.
            use_cache (bool): Whether to use cached results.
            max_retries: The maximum number of retry attempts.
            timeout: The timeout (in milliseconds) between retries.

        Returns:
            DendriteElement: The retrieved element.
        """

    @overload
    async def _get_element(
        self,
        prompt: str,
        only_one: Literal[False],
        use_cache: bool,
        max_retries,
        timeout,
    ) -> List[DendriteElement]:
        """
        Retrieves a list of Dendrite elements based on the provided prompt.

        Args:
            prompt (str): The prompt describing the elements to be retrieved.
            only_one (Literal[False]): Indicates that multiple elements should be retrieved.
            use_cache (bool): Whether to use cached results.
            max_retries: The maximum number of retry attempts.
            timeout: The timeout in seconds between retries.

        Returns:
            List[DendriteElement]: A list of retrieved elements.
        """

    async def _get_element(
        self, prompt: str, only_one: bool, use_cache: bool, max_retries, timeout
    ) -> Union[Optional[DendriteElement], List[DendriteElement]]:
        """
        Retrieves Dendrite elements based on the provided prompt, either a single element or a list of elements.

        This method sends a request with the prompt and retrieves the elements based on the `only_one` flag.
        If no elements are found within the specified retries, an exception is raised.

        Args:
            prompt (str): The prompt describing the elements to be retrieved.
            only_one (bool): Whether to retrieve only one element or a list of elements.
            use_cache (bool): Whether to use cached results.
            max_retries: The maximum number of retry attempts.
            timeout: The timeout (in milliseconds) between retries.

        Returns:
            Union[DendriteElement, List[DendriteElement]]: The retrieved element or list of elements.

        Raises:
            DendriteException: If no suitable elements are found within the specified retries.
        """

        llm_config = self.dendrite_browser.llm_config
        for attempt in range(max_retries):
            is_last_attempt = attempt == max_retries - 1
            force_not_use_cache = is_last_attempt

            logger.info(
                f"Getting element for '{prompt}' | Attempt {attempt + 1}/{max_retries}"
            )

            page_information = await self._get_page_information()

            dto = GetElementsDTO(
                page_information=page_information,
                llm_config=llm_config,
                prompt=prompt,
                use_cache=use_cache and not force_not_use_cache,
                only_one=only_one,
            )
            res = await self.browser_api_client.get_interactions_selector(dto)
            logger.debug(f"Got selectors: {res}")
            if not res.selectors:
                continue
                # raise DendriteException(
                #     message="Could not find suitable elements on the page.",
                #     screenshot_base64=page_information.screenshot_base64,
                # )

            for selector in reversed(res.selectors):

                dendrite_elements = await self._get_all_elements_from_selector(selector)
                if len(dendrite_elements) > 0:
                    logger.info(f"Got working selector: {selector}")
                    return dendrite_elements[0] if only_one else dendrite_elements

                if is_last_attempt:
                    logger.warning(
                        f"Last attempt: Failed to get elements from selector with cache disabled"
                    )
                else:
                    logger.warning(
                        f"Attempt {attempt + 1}: Failed to get elements from selector, trying again "
                    )

            if not is_last_attempt:
                await asyncio.sleep(timeout * 0.001)

        return None
