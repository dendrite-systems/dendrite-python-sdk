from typing import Any, Optional, Type, overload
from dendrite_sdk._api.dto.scrape_page_dto import ScrapePageDTO
from dendrite_sdk._core._type_spec import (
    JsonSchema,
    PydanticModel,
    TypeSpec,
    convert_to_type_spec,
    to_json_schema,
)
from dendrite_sdk._core.protocol.page_protocol import DendritePageProtocol


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
    ) -> bool: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[int],
        use_cache: bool = True,
    ) -> int: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[float],
        use_cache: bool = True,
    ) -> float: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: Type[str],
        use_cache: bool = True,
    ) -> str: ...

    @overload
    async def extract(
        self,
        prompt: Optional[str],
        type_spec: Type[PydanticModel],
        use_cache: bool = True,
    ) -> PydanticModel: ...

    @overload
    async def extract(
        self,
        prompt: Optional[str],
        type_spec: JsonSchema,
        use_cache: bool = True,
    ) -> JsonSchema: ...

    @overload
    async def extract(
        self,
        prompt: str,
        type_spec: None = None,
        use_cache: bool = True,
    ) -> Any: ...

    async def extract(
        self,
        prompt: Optional[str],
        type_spec: Optional[TypeSpec] = None,
        use_cache: bool = True,
    ) -> TypeSpec:
        """
        Extract data from a web page based on a prompt and optional type specification.

        Args:
            prompt (Optional[str]): The prompt to guide the extraction.
            type_spec (Optional[TypeSpec], optional): The type specification for the extracted data.
            use_cache (bool, optional): Whether to use cached results. Defaults to True.

        Returns:
            ScrapePageResponse: The extracted data wrapped in a ScrapePageResponse object.
        """
        json_schema = None
        if type_spec:
            json_schema = to_json_schema(type_spec)

        if prompt is None:
            prompt = ""

        page_information = await self._get_page_information()
        scrape_dto = ScrapePageDTO(
            page_information=page_information,
            llm_config=self.dendrite_browser.llm_config,
            prompt=prompt,
            return_data_json_schema=json_schema,
            use_screenshot=True,
            use_cache=use_cache,
        )
        res = await self.browser_api_client.scrape_page(scrape_dto)

        converted_res = res.return_data
        if type_spec is not None:
            converted_res = convert_to_type_spec(type_spec, res.return_data)

        res = converted_res

        return res
