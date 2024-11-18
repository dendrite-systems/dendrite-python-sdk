import json
import re
from typing import Any, Optional
from anthropic.types import TextBlock
from dendrite.browser.async_api._core.models.api_config import APIConfig
from dendrite.logic.local.dom.strip import mild_strip
from dendrite.logic.local.extract.prompts import create_script_prompt_segmented_html
from dendrite.logic.local.extract.scroll_agent import ScrollAgent
from dendrite.logic.local.get_element.hanifi_search import get_expanded_dom
from dendrite.models.dto.extract_dto import ExtractDTO
from dendrite.models.page_information import PageInformation

from bs4 import BeautifulSoup, Tag

from dendrite.models.response.extract_page_response import ExtractPageResponse
from ..code.code_session import CodeSession
from ..ask.image import segment_image
from dendrite_server_merge.core.llm.claude import async_claude_request

from dendrite_server_merge.logging import agent_logger

from loguru import logger



class ExtractAgent:
    def __init__(
        self, page_information: PageInformation, api_config: APIConfig, user_id: str
    ) -> None:
        self.page_information = page_information
        self.soup = BeautifulSoup(page_information.raw_html, "lxml")
        self.api_config = api_config
        self.messages = []
        self.generated_script: Optional[str] = None
        self.user_id = user_id
        self.scroll_agent = ScrollAgent(api_config, page_information)

    def get_generated_script(self):
        return self.generated_script

    async def write_and_run_script(
        self, extract_page_dto: ExtractDTO
    ) -> ExtractPageResponse:
        mild_soup = mild_strip(self.soup)

        search_terms = []

        segments = segment_image(
            extract_page_dto.page_information.screenshot_base64, segment_height=4000
        )

        scroll_result = await self.scroll_agent.scroll_through_page(
            extract_page_dto.combined_prompt,
            image_segments=segments,
        )

        if scroll_result.status == "error":
            return ExtractPageResponse(
                status="impossible",
                message=str(scroll_result.message),
                return_data=None,
                used_cache=False,
                created_script=None,
            )

        if scroll_result.status == "loading":
            return ExtractPageResponse(
                status="loading",
                message="This page is still loading. Please wait a bit longer.",
                return_data=None,
                used_cache=False,
                created_script=None,
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
                self.api_config,
            )
            if expanded:
                expanded_html = expanded[0]

        if expanded_html:
            return await self.code_script_from_found_expanded_html_tags(
                extract_page_dto, expanded_html, segments
            )
        else:
            compress_html = CompressHTML(
                mild_soup,
                exclude_dendrite_ids=False,
                focus_on_text=True,
                max_token_size=16000,
                max_size_per_element=10000,
                compression_multiplier=0.5,
            )
            expanded_html = await compress_html.compress(search_terms)
            return await self.code_script_from_compressed_html(
                extract_page_dto, expanded_html, segments, mild_soup
            )

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
        agent_logger.info("Starting code_script_from_found_expanded_html_tags method")
        messages = []

        user_prompt = create_script_prompt_segmented_html(
            extract_page_dto.combined_prompt,
            expanded_html,
            self.page_information.url,
        )
        agent_logger.debug(f"User prompt created: {user_prompt[:100]}...")

        content = [
            {
                "type": "text",
                "text": user_prompt,
            },
        ]

        messages = [
            {"role": "user", "content": content},
        ]

        iterations = 0
        max_retries = 10

        generated_script: str = ""
        response_data: Any | None = None

        while iterations <= max_retries:
            iterations += 1
            agent_logger.info(f"Starting iteration {iterations}")

            config = {
                "messages": messages,
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.3,
                "max_tokens": 1500,
            }
            res = await async_claude_request(config, self.api_config)
            if not isinstance(res.content[0], TextBlock):
                logger.error("Needs to be an text block: ", res)
                raise Exception("Needs to be an text block")

            text = res.content[0].text
            dict_res = {
                "role": "assistant",
                "content": text,
            }
            messages.append(dict_res)

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
                    agent_logger.debug("Processing code match")
                    generated_script = code_match.strip()
                    temp_code_session = CodeSession()
                    try:
                        variables = temp_code_session.exec_code(
                            generated_script,
                            self.soup,
                            self.page_information.raw_html,
                        )
                        agent_logger.debug("Code execution successful")
                    except Exception as e:
                        agent_logger.error(f"Code execution failed: {str(e)}")
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
                    agent_logger.debug("Processing JSON match")
                    extracted_json = json_match.strip()
                    data_dict = json.loads(extracted_json)
                    current_segment = 0
                    if "request_more_html" in data_dict:
                        agent_logger.info("Processing element indexes")
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
                            agent_logger.error(
                                f"Error processing element indexes: {str(e)}"
                            )
                            content = f"Error: {str(e)}"
                            messages.append({"role": "user", "content": content})
                            continue
                    elif "error" in data_dict:
                        agent_logger.error(f"Error in data_dict: {data_dict['error']}")
                        raise HTTPException(404, detail=data_dict["error"])
                    elif "success" in data_dict:
                        agent_logger.info("Script generation successful")
                        self.generated_script = generated_script

                        await upsert_script_in_db(
                            extract_page_dto.combined_prompt,
                            generated_script,
                            extract_page_dto.page_information.url,
                            user_id=self.user_id,
                        )
                        # agent_logger.debug(f"Response data: {response_data}")
                        return ExtractPageResponse(
                            status="success",
                            message=data_dict["success"],
                            return_data=response_data,
                            used_cache=False,
                            created_script=self.get_generated_script(),
                        )

        agent_logger.warning("Failed to create script after retrying several times")
        return ExtractPageResponse(
            status="failed",
            message="Failed to create script after retrying several times.",
            return_data=None,
            used_cache=False,
            created_script=self.get_generated_script(),
        )

    async def code_script_from_compressed_html(
        self, extract_page_dto: ExtractDTO, expanded_html, segments, mild_soup
    ):
        messages = []

        user_prompt = create_script_prompt_compressed_html(
            extract_page_dto.combined_prompt,
            expanded_html,
            self.page_information.url,
        )

        content = [
            {
                "type": "text",
                "text": user_prompt,
            },
        ]

        if extract_page_dto.use_screenshot:
            content += [
                {
                    "type": "text",
                    "text": "Here is a screenshot of the website:",
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": segments[0],
                    },
                },
            ]

        messages = [
            {"role": "user", "content": content},
        ]

        iterations = 0
        max_retries = 10

        generated_script: str = ""
        response_data: Any | None = None

        while iterations <= max_retries:
            iterations += 1

            config = {
                "messages": messages,
                "model": "claude-3-5-sonnet-20241022",
                "temperature": 0.3,
                "max_tokens": 1500,
            }
            res = await async_claude_request(config, self.api_config)
            if not isinstance(res.content[0], TextBlock):
                logger.error("Needs to be an text block: ", res)
                raise Exception("Needs to be an text block")

            text = res.content[0].text
            dict_res = {
                "role": "assistant",
                "content": text,
            }
            messages.append(dict_res)

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
                    generated_script = code_match.strip()
                    temp_code_session = CodeSession()
                    try:
                        variables = temp_code_session.exec_code(
                            generated_script,
                            self.soup,
                            self.page_information.raw_html,
                        )
                    except Exception as e:
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
                    extracted_json = json_match.strip()
                    data_dict = json.loads(extracted_json)
                    content = ""
                    if "d-ids" in data_dict:
                        try:

                            content += "Here is the expanded HTML:"
                            for d_id in data_dict["d-ids"]:
                                d_id_res = mild_soup.find(attrs={"d-id": d_id})

                                tag = None

                                if isinstance(d_id_res, Tag):
                                    tag = d_id_res

                                if tag:
                                    subsection_mild = mild_strip(tag)
                                    pretty = subsection_mild.prettify()
                                    if len(pretty) > 120000:
                                        compress_html = CompressHTML(
                                            subsection_mild,
                                            exclude_dendrite_ids=False,
                                            max_token_size=16000,
                                            max_size_per_element=10000,
                                            focus_on_text=True,
                                            compression_multiplier=0.3,
                                        )
                                        subsection_compressed_html = (
                                            await compress_html.compress()
                                        )
                                        content += f"\n\nThis expanded element with the d-id '{d_id}' was too large to inspect fully! Here is a compressed version of the element you selected, please inspect a smaller section of it:\n```html\n{subsection_compressed_html}\n```"
                                    else:
                                        subsection_mild = mild_strip(
                                            tag, keep_d_id=False
                                        )
                                        pretty = subsection_mild.prettify()
                                        content += f"\n\nExpanded element with the d-id '{d_id}':\n```html\n{pretty}\n```"
                                else:
                                    content += f"\n\nNo valid element could be found with the d-id or id '{d_id}'. Prefer using the d-id attribute."

                            content += "\n\nIf you cannot find the relevant data in this HTML, consider expanding a different region."
                            messages.append({"role": "user", "content": content})
                            continue
                        except Exception as e:
                            messages.append(
                                {"role": "user", "content": f"Error: {str(e)}"}
                            )
                            agent_logger.debug(f"role: user, content: Error: {str(e)}")
                    elif "error" in data_dict:
                        raise HTTPException(404, detail=data_dict["error"])
                    elif "success" in data_dict:
                        self.generated_script = generated_script

                        await upsert_script_in_db(
                            extract_page_dto.combined_prompt,
                            generated_script,
                            extract_page_dto.page_information.url,
                            user_id=self.user_id,
                        )

                        return ExtractPageResponse(
                            status="success",
                            message=data_dict["success"],
                            return_data=response_data,
                            used_cache=False,
                            created_script=self.get_generated_script(),
                        )

        return ExtractPageResponse(
            status="failed",
            message="Failed to create script after retrying several times.",
            return_data=None,
            used_cache=False,
            created_script=self.get_generated_script(),
        )
