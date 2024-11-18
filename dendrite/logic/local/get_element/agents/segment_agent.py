import re
import json
from typing import Annotated, List, Literal, Tuple, Union
from annotated_types import Len
from loguru import logger
from pydantic import BaseModel, ValidationError
from anthropic.types import Message, TextBlock

from dendrite.browser.async_api._core.models.api_config import APIConfig

from .agent import (
    AnthropicAgent,
)
from .prompts  import (
    SEGMENT_PROMPT,
)




class SegmentAgentSuccessResponse(BaseModel):
    reason: str
    status: Literal["success"]
    d_id: Annotated[List[str], Len(min_length=1)]
    index: int = 99999  # placeholder since the agent doesn't output this


class SegmentAgentFailureResponse(BaseModel):
    reason: str
    status: Literal["failed", "loading", "impossible"]
    index: int = 99999  # placeholder since the agent doesn't output this


SegmentAgentReponseType = Union[
    SegmentAgentSuccessResponse, SegmentAgentFailureResponse
]


def parse_claude_result(result: Message, index: int) -> SegmentAgentReponseType:
    json_pattern = r"```json(.*?)```"
    model = None

    if len(result.content) == 0 or not isinstance(result.content[0], TextBlock):
        return SegmentAgentFailureResponse(
            reason="No content from agent", status="failed", index=index
        )

    text = result.content[0].text

    if text is None:
        return SegmentAgentFailureResponse(
            reason="No content", status="failed", index=index
        )

    json_matches = re.findall(json_pattern, text, re.DOTALL)

    if not json_matches:
        return SegmentAgentFailureResponse(
            reason="No JSON matches", status="failed", index=index
        )

    json_match = json_matches[0]
    try:
        json_data = json.loads(json_match)
        if "d_id" in json_data and "reason" in json_data:
            ids = json_data["d_id"]
            if len(ids) == 0:
                logger.warning(
                    f"Success message was output, but no d_ids provided: {json_data}"
                )
                return SegmentAgentFailureResponse(
                    reason="No d_ids provided", status="failed", index=index
                )

            model = SegmentAgentSuccessResponse(
                reason=json_data["reason"],
                status="success",
                d_id=json_data["d_id"],
            )
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}")

    if model is None:
        try:
            model = SegmentAgentFailureResponse.model_validate_json(json_matches[0])
        except ValidationError as e:
            logger.bind(json=json_matches[0]).error(
                f"Failed to parse JSON: {e}",
            )
            model = SegmentAgentFailureResponse(
                reason="Failed to parse JSON", status="failed", index=index
            )

    model.index = index
    return model



async def extract_relevant_d_ids(
    prompt: str,
    segments: List[str],
    api_config: APIConfig,
    index: int,
) -> Tuple[int, int, SegmentAgentReponseType]:
    agent = AnthropicAgent(
        "claude-3-haiku-20240307", api_config, system_message=SEGMENT_PROMPT
    )
    message = ""
    for segment in segments:
        message += (
            f"""###### SEGMENT ######\n\n{segment}\n\n###### SEGMENT END ######\n\n"""
        )

    message += f"Can you get the d_ids of the elements that match the following description:\n\n{prompt} element\n\nIf you've selected an element you should NOT select another element that is a child of the element you've selected. It is important that you follow this."
    message += """\nOutput how you think. Think step by step. if there are multiple candidate elements return all of them. Don't make up d-id for elements if they are not present/don't match the description. Limit your reasoning to 2-3 sentences\nOnly include the json block – don't output an array, only ONE object."""

    max_retries = 3
    for attempt in range(max_retries):
        res = await agent.add_message(message)
        if res is None:
            message = "I didn't receive a response. Please try again."
            continue

        try:
            parsed_res = parse_claude_result(res, index)
            # If we successfully parsed the result, return it
            completion = res.usage.output_tokens if res.usage else 0
            prompt_token = res.usage.input_tokens if res.usage else 0
            return (prompt_token, completion, parsed_res)
        except Exception as e:
            # If we encounter a ValueError, ask the agent to correct its output
            logger.warning(f"Error in segment agent: {e}")
            message = f"An exception occurred in your output: {e}\n\nPlease correct your output and try again. Ensure you're providing a valid JSON response."

    # If we've exhausted all retries, return a failure response
    return (
        0,
        0,
        SegmentAgentFailureResponse(
            reason="Max retries reached without successful parsing",
            status="failed",
            index=index,
        ),
    )
