import asyncio
import time
from typing import Any, Callable, List, Optional, Type, overload

from loguru import logger

from dendrite.browser.async_api._utils import convert_to_type_spec, to_json_schema
from dendrite.logic.code.code_session import execute
from dendrite.models.dto.cached_extract_dto import CachedExtractDTO
from dendrite.models.dto.extract_dto import ExtractDTO
from dendrite.models.response.extract_response import ExtractResponse
from dendrite.models.scripts import Script

from ..manager.navigation_tracker import NavigationTracker
from ..protocol.page_protocol import DendritePageProtocol
from ..types import JsonSchema, PydanticModel, TypeSpec

CACHE_TIMEOUT = 5


class ExtractionMixin(DendritePageProtocol):
    """
    Mixin that provides extraction functionality for web pages.

    This mixin provides various `extract` methods that allow extracting
    different types of data (e.g., bool, int, float, string, Pydantic models, etc.)
    from a web page based on a given prompt.
    """

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[bool],
        use_cache: bool = True,
        timeout: int = 180,
    ) -> bool: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[int],
        use_cache: bool = True,
        timeout: int = 180,
    ) -> int: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[float],
        use_cache: bool = True,
        timeout: int = 180,
    ) -> float: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[str],
        use_cache: bool = True,
        timeout: int = 180,
    ) -> str: ...

    @overload
    async def extract(
        self,
        prompt: Optional[str],
        type_spec: Type[PydanticModel],
        use_cache: bool = True,
        timeout: int = 180,
    ) -> PydanticModel: ...

    @overload
    async def extract(
        self,
        prompt: Optional[str],
        type_spec: JsonSchema,
        use_cache: bool = True,
        timeout: int = 180,
    ) -> JsonSchema: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: None = None,
        use_cache: bool = True,
        timeout: int = 180,
    ) -> Any: ...

    async def extract(
        self,
        prompt: Optional[str],
        type_spec: Optional[TypeSpec] = None,
        use_cache: bool = True,
        timeout: int = 180,
    ) -> TypeSpec:
        """
        Extract data from a web page based on a prompt and optional type specification.
        Args:
            prompt (Optional[str]): The prompt to describe the information to extract.
            type_spec (Optional[TypeSpec], optional): The type specification for the extracted data.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            timeout (int, optional): Maximum time in milliseconds for the entire operation. If use_cache=True,
                up to 5000ms will be spent attempting to use cached scripts before falling back to the
                extraction agent for the remaining time that will attempt to generate a new script. Defaults to 15000 (15 seconds).

        Returns:
            ExtractResponse: The extracted data wrapped in a ExtractResponse object.
        Raises:
            TimeoutError: If the extraction process exceeds the specified timeout.
        """
        logger.info(f"Starting extraction with prompt: {prompt}")

        json_schema = None
        if type_spec:
            json_schema = to_json_schema(type_spec)
            logger.debug(f"Type specification converted to JSON schema: {json_schema}")

        if prompt is None:
            prompt = ""

        start_time = time.time()
        page = await self._get_page()
        navigation_tracker = NavigationTracker(page)
        navigation_tracker.start_nav_tracking()

        # First try using cached extraction if enabled
        if use_cache:
            logger.info("Testing cache")
            cached_result = await self._try_cached_extraction(prompt, json_schema)
            if cached_result:
                return convert_and_return_result(cached_result, type_spec)

        # If cache failed or disabled, proceed with extraction agent
        logger.info(
            "Using extraction agent to perform extraction, since no cache was found or failed."
        )
        result = await self._extract_with_agent(
            prompt,
            json_schema,
            timeout - (time.time() - start_time),
        )

        if result:
            return convert_and_return_result(result, type_spec)

        logger.error(f"Extraction failed after {time.time() - start_time:.2f} seconds")
        return None

    async def _try_cached_extraction(
        self,
        prompt: str,
        json_schema: Optional[JsonSchema],
    ) -> Optional[ExtractResponse]:
        """
        Attempts to extract data using cached scripts with exponential backoff.
        Only tries up to 5 most recent scripts.

        Args:
            prompt: The prompt describing what to extract
            json_schema: Optional JSON schema for type validation

        Returns:
            ExtractResponse if successful, None otherwise
        """
        page = await self._get_page()
        dto = CachedExtractDTO(url=page.url, prompt=prompt)
        scripts = await self.logic_engine.get_cached_scripts(dto)
        logger.debug(f"Found {len(scripts)} scripts in cache, {scripts}")
        if len(scripts) == 0:
            logger.debug(
                f"No scripts found in cache for prompt: {prompt} in domain: {page.url}"
            )
            return None

        async def try_cached_extract():
            page = await self._get_page()
            soup = await page._get_soup()
            # Take at most the last 5 scripts
            recent_scripts = scripts[-min(5, len(scripts)) :]
            for script in recent_scripts:
                res = await test_script(script, str(soup), json_schema)
                if res is not None:
                    return ExtractResponse(
                        status="success",
                        message="Re-used a preexisting script from cache with the same specifications.",
                        return_data=res,
                        created_script=script.script,
                    )

            return None

        return await _attempt_with_backoff_helper(
            "cached_extraction",
            try_cached_extract,
            CACHE_TIMEOUT,
        )

    async def _extract_with_agent(
        self,
        prompt: str,
        json_schema: Optional[JsonSchema],
        remaining_timeout: float,
    ) -> Optional[ExtractResponse]:
        """
        Attempts to extract data using the extraction agent with exponential backoff.

        Args:
            prompt: The prompt describing what to extract
            json_schema: Optional JSON schema for type validation
            remaining_timeout: Maximum time to spend on extraction

        Returns:
            ExtractResponse if successful, None otherwise
        """

        async def try_extract_with_agent():
            page = await self._get_page()
            page_information = await page.get_page_information(include_screenshot=True)
            extract_dto = ExtractDTO(
                page_information=page_information,
                prompt=prompt,
                return_data_json_schema=json_schema,
                use_screenshot=True,
            )

            res: ExtractResponse = await self.logic_engine.extract(extract_dto)

            if res.status == "impossible":
                logger.error(f"Impossible to extract data. Reason: {res.message}")
                return None

            if res.status == "success":
                logger.success(f"Extraction successful: '{res.message}'")
                return res

            return None

        return await _attempt_with_backoff_helper(
            "extraction_agent",
            try_extract_with_agent,
            remaining_timeout,
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


def convert_and_return_result(
    res: ExtractResponse, type_spec: Optional[TypeSpec]
) -> TypeSpec:
    converted_res = res.return_data
    if type_spec is not None:
        logger.debug("Converting extraction result to specified type")
        converted_res = convert_to_type_spec(type_spec, res.return_data)

    logger.info("Extraction process completed successfully")
    return converted_res


async def test_script(
    script: Script,
    raw_html: str,
    return_data_json_schema: Any,
) -> Optional[Any]:

    try:
        res = execute(script.script, raw_html, return_data_json_schema)
        return res
    except Exception as e:
        logger.debug(f"Script failed with error: {str(e)} ")
