import re
from typing import List, Optional, Tuple

from loguru import logger
from openai.types.chat import ChatCompletion
from pydantic import BaseModel

from dendrite.browser._common.types import Status
from dendrite.logic.llm.agent import Agent
from dendrite.logic.llm.config import LLMConfig

from ..hanifi_segment import SelectedTag
from .prompts import SELECT_PROMPT


class SelectAgentResponse(BaseModel):
    reason: str
    d_id: Optional[List[str]] = None
    status: Status


async def select_best_tag(
    expanded_html_tree: str,
    tags: List[SelectedTag],
    prompt: str,
    time_since_frame_navigated: Optional[float],
    llm_config: LLMConfig,
    return_several: bool = False,
) -> Tuple[int, int, Optional[SelectAgentResponse]]:

    agent = Agent(llm_config.get("select_agent"), system_prompt=SELECT_PROMPT)

    message = f"<ELEMENT_DESCRIPTION>\n{prompt}\n</ELEMENT_DESCRIPTION>"

    tags_str = "\n".join([f"d-id: {tag.d_id} - reason: '{tag.reason}'" for tag in tags])

    message += f"""\n\nA smaller and less intelligent AI agent has combed through the html document and found these elements that seems to match the element description:\n\n{tags_str}\n\nThis agent is very primitive however, so don't blindly trust it. Make sure you carefully look at this truncated version of the html document and do some proper reasoning in which you consider the different potential elements:\n\n```html\n{expanded_html_tree}\n```\n"""

    if return_several:
        message += f"""Please look at the HTML Tree and output a list of d-ids that matches the ELEMENT_DESCRIPTION."""
    else:
        message += f"""Please look at the HTML Tree and output the best d-id that matches the ELEMENT_DESCRIPTION. Only return ONE d-id."""

    if time_since_frame_navigated:
        message += f"""\n\nThis page was first loaded {round(time_since_frame_navigated, 2)} second(s) ago. If the page is blank or the data is not available on the current page it could be because the page is still loading.\n\nDon't return an element that isn't what the user asked for, in this case it is better to return `status: impossible` or `status: loading` if you think the page is still loading."""

    res = await agent.add_message(message)

    logger.info(f"Select agent response: {res}")

    parsed = await parse_select_output(res)

    # token_usage = res.usage.input_tokens + res.usage.output_tokens
    return (0, 0, parsed)


async def parse_select_output(text: str) -> Optional[SelectAgentResponse]:
    json_pattern = r"```json(.*?)```"

    json_matches = re.findall(json_pattern, text, re.DOTALL)

    if not json_matches:
        return None

    try:
        model = SelectAgentResponse.model_validate_json(json_matches[0])
    except Exception as e:
        model = None

    return model


async def parse_openai_select_response(
    result: ChatCompletion,
) -> Optional[SelectAgentResponse]:
    json_pattern = r"```json(.*?)```"

    # Ensure the result has a message and content field
    if len(result.choices) == 0 or result.choices[0].message.content is None:
        return None

    # Extract the text content
    text = result.choices[0].message.content

    # Find JSON formatted code block in the response text
    json_matches = re.findall(json_pattern, text, re.DOTALL)

    if not json_matches:
        return None

    try:
        # Attempt to validate and parse the JSON match
        model = SelectAgentResponse.model_validate_json(json_matches[0])
    except Exception as e:
        # In case of any error during parsing
        model = None

    return model
