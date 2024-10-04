import time
import time
from typing import Any, Optional, Type, overload
from dendrite_sdk.sync_api._api.dto.extract_dto import ExtractDTO
from dendrite_sdk.sync_api._core._type_spec import (
    JsonSchema,
    PydanticModel,
    TypeSpec,
    convert_to_type_spec,
    to_json_schema,
)
from dendrite_sdk.sync_api._core.protocol.page_protocol import DendritePageProtocol


class ExtractionMixin(DendritePageProtocol):
    """
    Mixin that provides extraction functionality for web pages.

    This mixin provides various `extract` methods that allow extracting
    different types of data (e.g., bool, int, float, string, Pydantic models, etc.)
    from a web page based on a given prompt.
    """

    @overload
    def extract(
        self,
        prompt: str,
        type_spec: Type[bool],
        use_cache: bool = True,
        timeout: int = 180,
    ) -> bool: ...

    @overload
    def extract(
        self,
        prompt: str,
        type_spec: Type[int],
        use_cache: bool = True,
        timeout: int = 180,
    ) -> int: ...

    @overload
    def extract(
        self,
        prompt: str,
        type_spec: Type[float],
        use_cache: bool = True,
        timeout: int = 180,
    ) -> float: ...

    @overload
    def extract(
        self,
        prompt: str,
        type_spec: Type[str],
        use_cache: bool = True,
        timeout: int = 180,
    ) -> str: ...

    @overload
    def extract(
        self,
        prompt: Optional[str],
        type_spec: Type[PydanticModel],
        use_cache: bool = True,
        timeout: int = 180,
    ) -> PydanticModel: ...

    @overload
    def extract(
        self,
        prompt: Optional[str],
        type_spec: JsonSchema,
        use_cache: bool = True,
        timeout: int = 180,
    ) -> JsonSchema: ...

    @overload
    def extract(
        self,
        prompt: str,
        type_spec: None = None,
        use_cache: bool = True,
        timeout: int = 180,
    ) -> Any: ...

    def extract(
        self,
        prompt: Optional[str],
        type_spec: Optional[TypeSpec] = None,
        use_cache: bool = True,
        timeout: int = 180,
    ) -> TypeSpec:
        """
        Extract data from a web page based on a prompt and optional type specification.

        Args:
            prompt (Optional[str]): The prompt to guide the extraction.
            type_spec (Optional[TypeSpec], optional): The type specification for the extracted data.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.
            timeout (int, optional): The maximum time to wait for extraction in seconds. Defaults to 180 seconds, which is 3 minutes.

        Returns:
            ExtractResponse: The extracted data wrapped in a ExtractResponse object.

        Raises:
            TimeoutError: If the extraction process exceeds the specified timeout.
        """
        json_schema = None
        if type_spec:
            json_schema = to_json_schema(type_spec)
        if prompt is None:
            prompt = ""
        init_start_time = time.time()
        page = self._get_page()
        page_information = page.get_page_information()
        extract_dto = ExtractDTO(
            page_information=page_information,
            api_config=self._get_dendrite_browser().api_config,
            prompt=prompt,
            return_data_json_schema=json_schema,
            use_screenshot=True,
            use_cache=use_cache,
        )
        delay = 1
        while True:
            elapsed_time = time.time() - init_start_time
            if elapsed_time > timeout:
                raise TimeoutError(
                    f"Extraction process exceeded the timeout of {timeout} seconds"
                )
            start_time = time.time()
            res = self._get_browser_api_client().extract(extract_dto)
            request_time = time.time() - start_time
            if res.status != "loading":
                break
            remaining_delay = max(0, delay - request_time)
            time.sleep(remaining_delay)
            delay = min(delay * 2, 20)
        converted_res = res.return_data
        if type_spec is not None:
            converted_res = convert_to_type_spec(type_spec, res.return_data)
        return converted_res
