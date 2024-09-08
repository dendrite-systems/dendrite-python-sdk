from typing import Optional, Type, overload

from dendrite_sdk._api.dto.ask_page_dto import AskPageDTO
from dendrite_sdk._core._type_spec import (
    JsonSchema,
    PydanticModel,
    TypeSpec,
    convert_to_type_spec,
    to_json_schema,
)
from dendrite_sdk._core.protocol.page_protocol import DendritePageProtocol
from dendrite_sdk._exceptions.dendrite_exception import DendriteException


class AskMixin(DendritePageProtocol):

    @overload
    async def ask(self, prompt: str, type_spec: Type[str]) -> str:
        """
        Asks a question about the current page and expects a response of type `str`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[str]): The expected return type, which is `str`.

        Returns:
            AskPageResponse[str]: The response object containing the result of type `str`.
        """

    @overload
    async def ask(self, prompt: str, type_spec: Type[bool]) -> bool:
        """
        Asks a question about the current page and expects a responseof type `bool`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[bool]): The expected return type, which is `bool`.

        Returns:
            AskPageResponse[bool]: The response object containing the result of type `bool`.
        """

    @overload
    async def ask(self, prompt: str, type_spec: Type[int]) -> int:
        """
        Asks a question about the current page and expects a response of type `int`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[int]): The expected return type, which is `int`.

        Returns:
            AskPageResponse[int]: The response object containing the result of type `int`.
        """

    @overload
    async def ask(self, prompt: str, type_spec: Type[float]) -> float:
        """
        Asks a question about the current page and expects a response of type `float`.

         Args:
             prompt (str): The question or prompt to be asked.
             type_spec (Type[float]): The expected return type, which is `float`.

         Returns:
             AskPageResponse[float]: The response object containing the result of type `float`.
        """

    @overload
    async def ask(self, prompt: str, type_spec: Type[PydanticModel]) -> PydanticModel:
        """
        Asks a question about the current page and expects a response of a custom `PydanticModel`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[PydanticModel]): The expected return type, which is a `PydanticModel`.

        Returns:
            AskPageResponse[PydanticModel]: The response object containing the result of the specified Pydantic model type.
        """

    @overload
    async def ask(self, prompt: str, type_spec: Type[JsonSchema]) -> JsonSchema:
        """
        Asks a question about the current page and expects a response conforming to a `JsonSchema`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[JsonSchema]): The expected return type, which is a `JsonSchema`.

        Returns:
            AskPageResponse[JsonSchema]: The response object containing the result conforming to the specified JSON schema.
        """

    @overload
    async def ask(self, prompt: str, type_spec: None = None) -> JsonSchema:
        """
        Asks a question without specifying a type and expects a response conforming to a default `JsonSchema`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (None, optional): The expected return type, which is `None` by default.

        Returns:
            AskPageResponse[JsonSchema]: The response object containing the result conforming to the default JSON schema.
        """

    async def ask(
        self,
        prompt: str,
        type_spec: Optional[TypeSpec] = None,
    ) -> TypeSpec:
        """
        Asks a question and processes the response based on the specified type.

        This method sends a request to ask a question with the specified prompt and processes the response.
        If a type specification is provided, the response is converted to the specified type. In case of failure,
        a DendriteException is raised with relevant details.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Optional[TypeSpec], optional): The expected return type, which can be a type or a schema. Defaults to None.

        Returns:
            AskPageResponse[Any]: The response object containing the result, converted to the specified type if provided.

        Raises:
            DendriteException: If the request fails, the exception includes the failure message and a screenshot.
        """
        llm_config = self.dendrite_browser.llm_config
        page_information = await self._get_page_information()

        schema = None
        if type_spec:
            schema = to_json_schema(type_spec)

        dto = AskPageDTO(
            page_information=page_information,
            llm_config=llm_config,
            prompt=prompt,
            return_schema=schema,
        )
        res = await self.browser_api_client.ask_page(dto)
        if res.status == "error":
            raise DendriteException(
                message=res.return_data,
                screenshot_base64=page_information.screenshot_base64,
            )

            # raise DendriteException(
            #     message=res.,
            #     screenshot_base64=page_information.screenshot_base64,
            # )

        converted_res = res.return_data
        if type_spec is not None:
            converted_res = convert_to_type_spec(type_spec, res.return_data)

        return converted_res
