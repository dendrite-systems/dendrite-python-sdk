import json
import re
import sys
from typing import Any, List, Optional

from loguru import logger

from dendrite.logic.cache.utils import save_script
from dendrite.logic.dom.strip import mild_strip
from dendrite.logic.extract.prompts import (
    LARGE_HTML_CHAR_TRUNCATE_LEN,
    create_script_prompt_segmented_html,
)

from dendrite.logic.extract.scroll_agent import ScrollAgent
from dendrite.logic.llm.agent import Agent
from dendrite.logic.get_element.hanifi_search import get_expanded_dom
from dendrite.logic.llm.token_count import token_count
from dendrite.models.dto.extract_dto import ExtractDTO
from dendrite.models.page_information import PageInformation
from dendrite.logic.llm.agent import Message

from bs4 import BeautifulSoup

from dendrite.models.response.extract_response import ExtractResponse
from ..code.code_session import CodeSession
from ..ask.image import segment_image
from ..llm.config import llm_config


class ExtractAgent(Agent):
    def __init__(
        self,
        page_information: PageInformation,
    ) -> None:
        super().__init__(llm_config.get("extract_agent"))
        self.page_information = page_information
        self.soup = BeautifulSoup(page_information.raw_html, "lxml")
        self.messages = []
        self.generated_script: Optional[str] = None
        self.llm_config = llm_config

    def get_generated_script(self):
        return self.generated_script

    async def write_and_run_script(
        self, extract_page_dto: ExtractDTO
    ) -> ExtractResponse:
        mild_soup = mild_strip(self.soup)

        search_terms = []

        segments = segment_image(
            extract_page_dto.page_information.screenshot_base64, segment_height=4000
        )

        scroll_agent = ScrollAgent(self.page_information)
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
                mild_soup,
                combined_prompt,
            )
            if expanded:
                expanded_html = expanded[0]

        if expanded_html:
            return await self.code_script_from_found_expanded_html_tags(
                extract_page_dto, expanded_html, segments
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
        self, extract_page_dto: ExtractDTO, expanded_html, segments
    ):

        agent_logger = logger.bind(
            scope="extract", step="generate_code"
        )  # agent_logger.info("Starting code_script_from_found_expanded_html_tags method")
        agent_logger.remove()
        fmt = "<green>{time: HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        agent_logger.add(sys.stderr, level="DEBUG", format=fmt)
        messages = []

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

        generated_script: str = ""
        response_data: Any | None = None

        while iterations <= max_retries:
            iterations += 1
            agent_logger.debug(f"Code generation | Iteration: {iterations}")

            text = await self.call_llm(messages)
            messages.append({"role": "assistant", "content": text})

            json_pattern = r"```json(.*?)```"
            code_pattern = r"```python(.*?)```"

            if text:
                json_matches = re.findall(json_pattern, text, re.DOTALL)
                code_matches = re.findall(code_pattern, text, re.DOTALL)

                if len(json_matches) + len(code_matches) > 1:
                    content = "Error: Please output only one action at a time (either JSON or Python code, not both)."
                    messages.append({"role": "user", "content": content})
                    continue

                for code_match in code_matches:
                    # agent_logger.debug("Processing code match")
                    generated_script = code_match.strip()
                    temp_code_session = CodeSession()
                    try:
                        variables = temp_code_session.exec_code(
                            generated_script,
                            self.soup,
                            self.page_information.raw_html,
                        )
                        # agent_logger.debug("Code execution successful")
                    except Exception as e:
                        # agent_logger.error(f"Code execution failed: {str(e)}")
                        content = f"Error: {str(e)}"
                        messages.append({"role": "user", "content": content})
                        continue

                    try:
                        if "response_data" in variables:
                            response_data = variables["response_data"]
                            # agent_logger.debug(f"Response data: {response_data}")

                            if extract_page_dto.return_data_json_schema != None:
                                temp_code_session.validate_response(
                                    extract_page_dto.return_data_json_schema,
                                    response_data,
                                )

                            llm_readable_exec_res = (
                                temp_code_session.llm_readable_exec_res(
                                    variables,
                                    extract_page_dto.combined_prompt,
                                    iterations,
                                    max_retries,
                                )
                            )

                            messages.append(
                                {"role": "user", "content": llm_readable_exec_res}
                            )
                            continue
                        else:
                            content = (
                                f"Error: You need to add the variable 'response_data'"
                            )
                            messages.append(
                                {
                                    "role": "user",
                                    "content": content,
                                }
                            )
                            continue
                    except Exception as e:
                        llm_readable_exec_res = temp_code_session.llm_readable_exec_res(
                            variables,
                            extract_page_dto.combined_prompt,
                            iterations,
                            max_retries,
                        )
                        content = f"Error: Failed to validate `response_data`. Exception: {e}. {llm_readable_exec_res}"
                        messages.append(
                            {
                                "role": "user",
                                "content": content,
                            }
                        )
                        continue

                for json_match in json_matches:
                    # agent_logger.debug("Processing JSON match")
                    extracted_json = json_match.strip()
                    data_dict = json.loads(extracted_json)
                    current_segment = 0
                    if "request_more_html" in data_dict:
                        # agent_logger.info("Processing element indexes")
                        try:
                            current_segment += 1
                            content = f"""Here is more of the HTML:\n```html\n{expanded_html[LARGE_HTML_CHAR_TRUNCATE_LEN*current_segment:LARGE_HTML_CHAR_TRUNCATE_LEN*(current_segment+1)]}\n```"""
                            if len(expanded_html) > LARGE_HTML_CHAR_TRUNCATE_LEN * (
                                current_segment + 1
                            ):
                                content += "\nThere is still more HTML to see. You can request more if needed."
                            else:
                                content += "\nThis is the end of the HTML content."
                            messages.append({"role": "user", "content": content})
                            continue
                        except Exception as e:
                            # agent_logger.error(
                            #     f"Error processing element indexes: {str(e)}"
                            # )
                            content = f"Error: {str(e)}"
                            messages.append({"role": "user", "content": content})
                            continue
                    elif "error" in data_dict:
                        # agent_logger.error(f"Error in data_dict: {data_dict['error']}")
                        raise Exception(data_dict["error"])
                    elif "success" in data_dict:
                        # agent_logger.info("Script generation successful")

                        self.generated_script = generated_script
                        save_script(
                            self.generated_script,
                            extract_page_dto.combined_prompt,
                            self.page_information.url,
                        )

                        # agent_logger.debug(f"Response data: {response_data}")
                        return ExtractResponse(
                            status="success",
                            message=data_dict["success"],
                            return_data=response_data,
                            created_script=self.get_generated_script(),
                        )

        # agent_logger.warning("Failed to create script after retrying several times")
        return ExtractResponse(
            status="failed",
            message="Failed to create script after retrying several times.",
            return_data=None,
            created_script=self.get_generated_script(),
        )
