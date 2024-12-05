import time
import time
from typing import Optional, Type, overload
from loguru import logger
from dendrite.browser._common._exceptions.dendrite_exception import DendriteException
from dendrite.browser.sync_api._utils import convert_to_type_spec, to_json_schema
from dendrite.models.dto.ask_page_dto import AskPageDTO
from ..protocol.page_protocol import DendritePageProtocol
from ..types import JsonSchema, PydanticModel, TypeSpec

TIMEOUT_INTERVAL = [150, 450, 1000]


class AskMixin(DendritePageProtocol):

    @overload
    def ask(self, prompt: str, type_spec: Type[str]) -> str:
        """
        Asks a question about the current page and expects a response of type `str`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[str]): The expected return type, which is `str`.

        Returns:
            AskPageResponse[str]: The response object containing the result of type `str`.
        """

    @overload
    def ask(self, prompt: str, type_spec: Type[bool]) -> bool:
        """
        Asks a question about the current page and expects a responseof type `bool`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[bool]): The expected return type, which is `bool`.

        Returns:
            AskPageResponse[bool]: The response object containing the result of type `bool`.
        """

    @overload
    def ask(self, prompt: str, type_spec: Type[int]) -> int:
        """
        Asks a question about the current page and expects a response of type `int`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[int]): The expected return type, which is `int`.

        Returns:
            AskPageResponse[int]: The response object containing the result of type `int`.
        """

    @overload
    def ask(self, prompt: str, type_spec: Type[float]) -> float:
        """
        Asks a question about the current page and expects a response of type `float`.

         Args:
             prompt (str): The question or prompt to be asked.
             type_spec (Type[float]): The expected return type, which is `float`.

         Returns:
             AskPageResponse[float]: The response object containing the result of type `float`.
        """

    @overload
    def ask(self, prompt: str, type_spec: Type[PydanticModel]) -> PydanticModel:
        """
        Asks a question about the current page and expects a response of a custom `PydanticModel`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[PydanticModel]): The expected return type, which is a `PydanticModel`.

        Returns:
            AskPageResponse[PydanticModel]: The response object containing the result of the specified Pydantic model type.
        """

    @overload
    def ask(self, prompt: str, type_spec: Type[JsonSchema]) -> JsonSchema:
        """
        Asks a question about the current page and expects a response conforming to a `JsonSchema`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (Type[JsonSchema]): The expected return type, which is a `JsonSchema`.

        Returns:
            AskPageResponse[JsonSchema]: The response object containing the result conforming to the specified JSON schema.
        """

    @overload
    def ask(self, prompt: str, type_spec: None = None) -> JsonSchema:
        """
        Asks a question without specifying a type and expects a response conforming to a default `JsonSchema`.

        Args:
            prompt (str): The question or prompt to be asked.
            type_spec (None, optional): The expected return type, which is `None` by default.

        Returns:
            AskPageResponse[JsonSchema]: The response object containing the result conforming to the default JSON schema.
        """

    def ask(
        self, prompt: str, type_spec: Optional[TypeSpec] = None, timeout: int = 15000
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
        start_time = time.time()
        attempt_start = start_time
        attempt = -1
        while True:
            attempt += 1
            current_timeout = (
                TIMEOUT_INTERVAL[attempt]
                if len(TIMEOUT_INTERVAL) > attempt
                else TIMEOUT_INTERVAL[-1] * 1.75
            )
            elapsed_time = time.time() - start_time
            remaining_time = timeout * 0.001 - elapsed_time
            if remaining_time <= 0:
                logger.warning(
                    f"Timeout reached for '{prompt}' after {attempt + 1} attempts"
                )
                break
            prev_attempt_time = time.time() - attempt_start
            sleep_time = min(
                max(current_timeout * 0.001 - prev_attempt_time, 0), remaining_time
            )
            logger.debug(f"Waiting for {sleep_time} seconds before retrying")
            time.sleep(sleep_time)
            attempt_start = time.time()
            logger.info(f"Asking '{prompt}' | Attempt {attempt + 1}")
            page = self._get_page()
            page_information = page.get_page_information()
            schema = to_json_schema(type_spec) if type_spec else None
            if elapsed_time < 5:
                time_prompt = f"This page was loaded {elapsed_time} seconds ago, so it might still be loading. If the page is still loading, return failed status."
            else:
                time_prompt = ""
            entire_prompt = prompt + time_prompt
            dto = AskPageDTO(
                page_information=page_information,
                prompt=entire_prompt,
                return_schema=schema,
            )
            try:
                res = self.logic_engine.ask_page(dto)
                logger.debug(f"Got response in {time.time() - attempt_start} seconds")
                if res.status == "error":
                    logger.warning(
                        f"Error response on attempt {attempt + 1}: {res.return_data}"
                    )
                    continue
                converted_res = res.return_data
                if type_spec is not None:
                    converted_res = convert_to_type_spec(type_spec, res.return_data)
                return converted_res
            except Exception as e:
                logger.error(f"Exception occurred on attempt {attempt + 1}: {str(e)}")
                if attempt == len(TIMEOUT_INTERVAL) - 1:
                    raise
        raise DendriteException(
            message=f"Failed to get response for '{prompt}' after {attempt + 1} attempts",
            screenshot_base64=page_information.screenshot_base64,
        )
