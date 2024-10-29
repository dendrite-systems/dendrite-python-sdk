import asyncio
import time
from typing import Any, Optional, Type, overload, List
from dendrite.async_api._api.dto.extract_dto import ExtractDTO
from dendrite.async_api._api.response.cache_extract_response import (
    CacheExtractResponse,
)
from dendrite.async_api._api.response.extract_response import ExtractResponse
from dendrite.async_api._core._type_spec import (
    JsonSchema,
    PydanticModel,
    TypeSpec,
    convert_to_type_spec,
    to_json_schema,
)
from dendrite.async_api._core.protocol.page_protocol import DendritePageProtocol
from dendrite.async_api._core._managers.navigation_tracker import NavigationTracker
from loguru import logger


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

        # Check if a script exists in the cache
        if use_cache:
            cache_available = await check_if_extract_cache_available(
                self, prompt, json_schema
            )

            if cache_available:
                logger.info("Cache available, attempting to use cached extraction")
                result = await attempt_extraction_with_backoff(
                    self,
                    prompt,
                    json_schema,
                    remaining_timeout=CACHE_TIMEOUT,
                    only_use_cache=True,
                )
                if result:
                    return convert_and_return_result(result, type_spec)

        logger.info(
            "Using extraction agent to perform extraction, since no cache was found or failed."
        )
        result = await attempt_extraction_with_backoff(
            self,
            prompt,
            json_schema,
            remaining_timeout=timeout - (time.time() - start_time),
            only_use_cache=False,
        )

        if result:
            return convert_and_return_result(result, type_spec)

        logger.error(f"Extraction failed after {time.time() - start_time:.2f} seconds")
        return None


async def check_if_extract_cache_available(
    obj: DendritePageProtocol, prompt: str, json_schema: Optional[JsonSchema]
) -> bool:
    page = await obj._get_page()
    page_information = await page.get_page_information(include_screenshot=False)
    dto = ExtractDTO(
        page_information=page_information,
        api_config=obj._get_dendrite_browser().api_config,
        prompt=prompt,
        return_data_json_schema=json_schema,
    )
    cache_response: CacheExtractResponse = (
        await obj._get_browser_api_client().check_extract_cache(dto)
    )
    return cache_response.exists


async def attempt_extraction_with_backoff(
    obj: DendritePageProtocol,
    prompt: str,
    json_schema: Optional[JsonSchema],
    remaining_timeout: float = 180.0,
    only_use_cache: bool = False,
) -> Optional[ExtractResponse]:
    TIMEOUT_INTERVAL: List[float] = [0.15, 0.45, 1.0, 2.0, 4.0, 8.0]
    total_elapsed_time = 0
    start_time = time.time()

    for current_timeout in TIMEOUT_INTERVAL:
        if total_elapsed_time >= remaining_timeout:
            logger.error(f"Timeout reached after {total_elapsed_time:.2f} seconds")
            return None

        request_start_time = time.time()
        page = await obj._get_page()
        page_information = await page.get_page_information(
            include_screenshot=not only_use_cache
        )
        extract_dto = ExtractDTO(
            page_information=page_information,
            api_config=obj._get_dendrite_browser().api_config,
            prompt=prompt,
            return_data_json_schema=json_schema,
            use_screenshot=True,
            use_cache=only_use_cache,
            force_use_cache=only_use_cache,
        )

        res = await obj._get_browser_api_client().extract(extract_dto)
        request_duration = time.time() - request_start_time

        if res.status == "impossible":
            logger.error(f"Impossible to extract data. Reason: {res.message}")
            return None

        if res.status == "success":
            logger.success(
                f"Extraction successful: '{res.message}'\nUsed cache: {res.used_cache}\nUsed script:\n\n{res.created_script}"
            )
            return res

        sleep_duration = max(0, current_timeout - request_duration)
        logger.info(
            f"Extraction attempt failed. Status: {res.status}\nMessage: {res.message}\nSleeping for {sleep_duration:.2f} seconds"
        )
        await asyncio.sleep(sleep_duration)
        total_elapsed_time = time.time() - start_time

    logger.error(
        f"All extraction attempts failed after {total_elapsed_time:.2f} seconds"
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
