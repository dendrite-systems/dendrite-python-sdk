import asyncio
import time
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Union,
    overload,
)

from bs4 import BeautifulSoup
from loguru import logger

from .._utils import _get_all_elements_from_selector_soup
from ..dendrite_element import AsyncElement

if TYPE_CHECKING:
    from ..dendrite_page import AsyncPage

from dendrite.models.dto.cached_selector_dto import CachedSelectorDTO
from dendrite.models.dto.get_elements_dto import GetElementsDTO

from ..protocol.page_protocol import DendritePageProtocol

CACHE_TIMEOUT = 5


class GetElementMixin(DendritePageProtocol):
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
            timeout (int, optional): Maximum time in milliseconds for the entire operation. If use_cache=True,
                up to 5000ms will be spent attempting to use cached selectors before falling back to the
                find element agent for the remaining time. Defaults to 15000 (15 seconds).

        Returns:
            AsyncElement: The retrieved element.
        """
        return await self._get_element(
            prompt,
            only_one=True,
            use_cache=use_cache,
            timeout=timeout / 1000,
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
            timeout (int, optional): Maximum time in milliseconds for the entire operation. If use_cache=True,
                up to 5000ms will be spent attempting to use cached selectors before falling back to the
                find element agent for the remaining time. Defaults to 15000 (15 seconds).

        Returns:
            AsyncElement: The retrieved element.
        """

    @overload
    async def _get_element(
        self,
        prompt_or_elements: str,
        only_one: Literal[False],
        use_cache: bool,
        timeout,
    ) -> List[AsyncElement]:
        """
        Retrieves a list of Dendrite elements based on the provided prompt.

        Args:
            prompt (str): The prompt describing the elements to be retrieved.
            only_one (Literal[False]): Indicates that multiple elements should be retrieved.
            use_cache (bool): Whether to use cached results.
            timeout (int, optional): Maximum time in milliseconds for the entire operation. If use_cache=True,
                up to 5000ms will be spent attempting to use cached selectors before falling back to the
                find element agent for the remaining time. Defaults to 15000 (15 seconds).

        Returns:
            List[AsyncElement]: A list of retrieved elements.
        """

    async def _get_element(
        self,
        prompt_or_elements: str,
        only_one: bool,
        use_cache: bool,
        timeout: float,
    ) -> Union[
        Optional[AsyncElement],
        List[AsyncElement],
    ]:
        """
        Retrieves Dendrite elements based on the provided prompt, either a single element or a list of elements.

        This method sends a request with the prompt and retrieves the elements based on the `only_one` flag.

        Args:
            prompt_or_elements (Union[str, Dict[str, str]]): The prompt or dictionary of prompts for element retrieval.
            only_one (bool): Whether to retrieve only one element or a list of elements.
            use_cache (bool): Whether to use cached results.
            timeout (int, optional): Maximum time in milliseconds for the entire operation. If use_cache=True,
                up to 5000ms will be spent attempting to use cached selectors before falling back to the
                find element agent for the remaining time. Defaults to 15000 (15 seconds).

        Returns:
            Union[AsyncElement, List[AsyncElement], AsyncElementsResponse]: The retrieved element, list of elements, or response object.
        """

        logger.info(f"Getting element for prompt: '{prompt_or_elements}'")
        start_time = time.time()
        page = await self._get_page()
        soup = await page._get_soup()

        if use_cache:
            cached_elements = await self._try_cached_selectors(
                page, soup, prompt_or_elements, only_one
            )
            if cached_elements:
                return cached_elements

        # Now that no cached selectors were found or they failed repeatedly, let's use the find element agent
        logger.info(
            "Proceeding to use the find element agent to find the requested elements."
        )
        res = await try_get_element(
            self,
            prompt_or_elements,
            only_one,
            remaining_timeout=timeout - (time.time() - start_time),
        )
        if res:
            return res

        logger.error(
            f"Failed to retrieve elements within the specified timeout of {timeout} seconds"
        )
        return None

    async def _try_cached_selectors(
        self,
        page: "AsyncPage",
        soup: BeautifulSoup,
        prompt: str,
        only_one: bool,
    ) -> Union[Optional[AsyncElement], List[AsyncElement]]:
        """
        Attempts to retrieve elements using cached selectors with exponential backoff.

        Args:
            page: The current page object
            soup: The BeautifulSoup object of the current page
            prompt: The prompt to search for
            only_one: Whether to return only one element

        Returns:
            The found elements if successful, None otherwise
        """
        dto = CachedSelectorDTO(url=page.url, prompt=prompt)
        selectors = await self.logic_engine.get_cached_selectors(dto)

        if len(selectors) == 0:
            logger.debug("No cached selectors found")
            return None

        logger.debug("Attempting to use cached selectors with backoff")
        # Take at most the last 5 selectors
        recent_selectors = selectors[-min(5, len(selectors)) :]
        str_selectors = list(map(lambda x: x.selector, recent_selectors))

        async def try_cached_selectors():
            return await get_elements_from_selectors_soup(
                page, soup, str_selectors, only_one
            )

        return await _attempt_with_backoff_helper(
            "cached_selectors",
            try_cached_selectors,
            timeout=CACHE_TIMEOUT,
        )


async def _attempt_with_backoff_helper(
    operation_name: str,
    operation: Callable,
    timeout: float,
    backoff_intervals: List[float] = [0.15, 0.45, 1.0, 2.0, 4.0, 8.0],
) -> Optional[Any]:
    """
    Generic helper function that implements exponential backoff for operations.

    Args:
        operation_name: Name of the operation for logging
        operation: Async function to execute
        timeout: Maximum time to spend attempting the operation
        backoff_intervals: List of timeouts between attempts

    Returns:
        The result of the operation if successful, None otherwise
    """
    total_elapsed_time = 0
    start_time = time.time()

    for i, current_timeout in enumerate(backoff_intervals):
        if total_elapsed_time >= timeout:
            logger.error(f"Timeout reached after {total_elapsed_time:.2f} seconds")
            return None

        request_start_time = time.time()
        result = await operation()
        request_duration = time.time() - request_start_time

        if result:
            return result

        sleep_duration = max(0, current_timeout - request_duration)
        logger.info(
            f"{operation_name} attempt {i+1} failed. Sleeping for {sleep_duration:.2f} seconds"
        )
        await asyncio.sleep(sleep_duration)
        total_elapsed_time = time.time() - start_time

    logger.error(
        f"All {operation_name} attempts failed after {total_elapsed_time:.2f} seconds"
    )
    return None


async def try_get_element(
    obj: DendritePageProtocol,
    prompt_or_elements: Union[str, Dict[str, str]],
    only_one: bool,
    remaining_timeout: float,
) -> Union[Optional[AsyncElement], List[AsyncElement]]:

    async def _try_get_element():
        page = await obj._get_page()
        page_information = await page.get_page_information()
        dto = GetElementsDTO(
            page_information=page_information,
            prompt=prompt_or_elements,
            only_one=only_one,
        )
        res = await obj.logic_engine.get_element(dto)

        if res.status == "impossible":
            logger.error(
                f"Impossible to get elements for '{prompt_or_elements}'. Reason: {res.message}"
            )
            return None

        if res.status == "success":
            logger.success(f"d[id]: {res.d_id} Selectors:{res.selectors}")
            if res.selectors is not None:
                return await get_elements_from_selectors_soup(
                    page, await page._get_previous_soup(), res.selectors, only_one
                )
        return None

    return await _attempt_with_backoff_helper(
        "find_element_agent",
        _try_get_element,
        remaining_timeout,
    )


async def get_elements_from_selectors_soup(
    page: "AsyncPage",
    soup: BeautifulSoup,
    selectors: List[str],
    only_one: bool,
) -> Union[Optional[AsyncElement], List[AsyncElement]]:

    for selector in reversed(selectors):
        dendrite_elements = await _get_all_elements_from_selector_soup(
            selector, soup, page
        )

        if len(dendrite_elements) > 0:
            return dendrite_elements[0] if only_one else dendrite_elements

    return None
