import json
import re
import sys
from typing import List, Union

from bs4 import BeautifulSoup

from dendrite import logger

from dendrite.logic.config import Config
from dendrite.logic.dom.strip import mild_strip
from dendrite.logic.extract.cache import save_script
from dendrite.logic.extract.prompts import (
    LARGE_HTML_CHAR_TRUNCATE_LEN,
    create_script_prompt_segmented_html,
)
from dendrite.logic.extract.scroll_agent import ScrollAgent
from dendrite.logic.get_element.hanifi_search import get_expanded_dom
from dendrite.logic.llm.agent import Agent, Message
from dendrite.logic.llm.token_count import token_count
from dendrite.models.dto.extract_dto import ExtractDTO
from dendrite.models.page_information import PageInformation
from dendrite.models.response.extract_response import ExtractResponse

from ..ask.image import segment_image
from ..code.code_session import CodeSession


class ExtractAgent(Agent):
    def __init__(self, page_information: PageInformation, config: Config) -> None:
        super().__init__(config.llm_config.get("extract_agent"))
        self.page_information = page_information
        self.soup = BeautifulSoup(page_information.raw_html, "lxml")
        self.messages = []
        self.current_segment = 0
        self.config = config

    async def write_and_run_script(
        self, extract_page_dto: ExtractDTO
    ) -> ExtractResponse:
        mild_soup = mild_strip(self.soup)

        segments = segment_image(
            extract_page_dto.page_information.screenshot_base64, segment_height=4000
        )

        scroll_agent = ScrollAgent(
            self.page_information, llm_config=self.config.llm_config
        )
        scroll_result = await scroll_agent.scroll_through_page(
            extract_page_dto.combined_prompt,
            image_segments=segments,
        )

        if scroll_result.status == "error":
            return ExtractResponse(
                status="impossible",
                message=str(scroll_result.message),
            )

        if scroll_result.status == "loading":
            return ExtractResponse(
                status="loading",
                message="This page is still loading. Please wait a bit longer.",
            )

        expanded_html = None

        if scroll_result.element_to_inspect_html:
            combined_prompt = (
                "Get these elements (make sure you only return element that you are confident that these are the correct elements, it's OK to not select any elements):\n- "
                + "\n- ".join(scroll_result.element_to_inspect_html)
            )
            expanded = await get_expanded_dom(
                mild_soup, combined_prompt, self.config.llm_config
            )
            if expanded:
                expanded_html = expanded[0]

        if expanded_html:
            return await self.code_script_from_found_expanded_html_tags(
                extract_page_dto, expanded_html
            )

        raise Exception("Failed to extract data from the page")  # TODO: skriv bättre

    def segment_large_tag(self, tag):
        segments = []
        current_segment = ""
        current_tokens = 0
        for line in tag.split("\n"):
            line_tokens = token_count(line)
            if current_tokens + line_tokens > 4000:
                segments.append(current_segment)
                current_segment = line
                current_tokens = line_tokens
            else:
                current_segment += line + "\n"
                current_tokens += line_tokens
        if current_segment:
            segments.append(current_segment)
        return segments

    async def code_script_from_found_expanded_html_tags(
        self, extract_page_dto: ExtractDTO, expanded_html
    ):

        agent_logger = logger.bind(scope="extract", step="generate_code")

        user_prompt = create_script_prompt_segmented_html(
            extract_page_dto.combined_prompt,
            expanded_html,
            self.page_information.url,
        )
        # agent_logger.debug(f"User prompt created: {user_prompt[:100]}...")

        content = {
            "type": "text",
            "text": user_prompt,
        }

        messages: List[Message] = [
            {"role": "user", "content": user_prompt},
        ]

        iterations = 0
        max_retries = 10

        for iterations in range(max_retries):
            agent_logger.debug(f"Code generation | Iteration: {iterations}")

            text = await self.call_llm(messages)
            messages.append({"role": "assistant", "content": text})

            json_pattern = r"```json(.*?)```"
            code_pattern = r"```python(.*?)```"

            if text is None:
                content = "Error: Failed to generate content."
                messages.append({"role": "user", "content": content})
                continue

            json_matches = re.findall(json_pattern, text, re.DOTALL)
            code_matches = re.findall(code_pattern, text, re.DOTALL)

            if len(json_matches) + len(code_matches) > 1:
                content = "Error: Please output only one action at a time (either JSON or Python code, not both)."
                messages.append({"role": "user", "content": content})
                continue

            if code_matches:
                self.generated_script = code_matches[0].strip()
                result = await self._handle_code_match(
                    code_matches[0].strip(),
                    messages,
                    iterations,
                    max_retries,
                    extract_page_dto,
                    agent_logger,
                )

                messages.extend(result)
                continue

            elif json_matches:
                result = self._handle_json_match(json_matches[0], expanded_html)
                if isinstance(result, ExtractResponse):
                    save_script(
                        self.generated_script,
                        extract_page_dto.combined_prompt,
                        self.page_information.url,
                        cache=self.config.extract_cache,
                    )
                    return result
                elif isinstance(result, list):
                    messages.extend(result)
                    continue
            else:
                # If neither code nor json matches found, send error message
                content = "Error: Could not find valid code or JSON in the assistant's response."
                messages.append({"role": "user", "content": content})
                continue

        # agent_logger.warning("Failed to create script after retrying several times")
        return ExtractResponse(
            status="failed",
            message="Failed to create script after retrying several times.",
            return_data=None,
            created_script=self.generated_script,
        )

    async def _handle_code_match(
        self,
        generated_script: str,
        messages: List[Message],
        iterations,
        max_retries,
        extract_page_dto: ExtractDTO,
        agent_logger,
    ) -> List[Message]:
        temp_code_session = CodeSession()

        try:
            variables = temp_code_session.exec_code(
                generated_script, self.soup, self.page_information.raw_html
            )

            if "response_data" not in variables:
                return [
                    {
                        "role": "user",
                        "content": "Error: You need to add the variable 'response_data'",
                    }
                ]

            self.response_data = variables["response_data"]

            if extract_page_dto.return_data_json_schema:
                temp_code_session.validate_response(
                    extract_page_dto.return_data_json_schema, self.response_data
                )

            llm_readable_exec_res = temp_code_session.llm_readable_exec_res(
                variables,
                extract_page_dto.combined_prompt,
                iterations,
                max_retries,
            )

            return [{"role": "user", "content": llm_readable_exec_res}]

        except Exception as e:
            return [{"role": "user", "content": f"Error: {str(e)}"}]

    def _handle_json_match(
        self, json_str: str, expanded_html: str
    ) -> Union[ExtractResponse, List[Message]]:
        try:
            data_dict = json.loads(json_str)

            if "request_more_html" in data_dict:
                return self._handle_more_html_request(expanded_html)

            if "error" in data_dict:
                raise Exception(data_dict["error"])

            if "success" in data_dict:
                return ExtractResponse(
                    status="success",
                    message=data_dict["success"],
                    return_data=self.response_data,
                    created_script=self.generated_script,
                )
            return [
                {
                    "role": "user",
                    "content": "Error: JSON response does not specify a valid action.",
                }
            ]

        except Exception as e:
            return [{"role": "user", "content": f"Error: {str(e)}"}]

    def _handle_more_html_request(self, expanded_html: str) -> List[Message]:

        if LARGE_HTML_CHAR_TRUNCATE_LEN * (self.current_segment + 1) >= len(
            expanded_html
        ):
            return [{"role": "user", "content": "There is no more HTML to show."}]

        self.current_segment += 1
        start = LARGE_HTML_CHAR_TRUNCATE_LEN * self.current_segment
        end = min(
            LARGE_HTML_CHAR_TRUNCATE_LEN * (self.current_segment + 1),
            len(expanded_html),
        )

        content = (
            f"""Here is more of the HTML:\n```html\n{expanded_html[start:end]}\n```"""
        )

        if len(expanded_html) > end:
            content += (
                "\nThere is still more HTML to see. You can request more if needed."
            )
        else:
            content += "\nThis is the end of the HTML content."

        return [{"role": "user", "content": content}]
