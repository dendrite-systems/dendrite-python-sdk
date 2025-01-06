import json
import re
from typing import Annotated, List, Literal, Union

from annotated_types import Len
from loguru import logger
from pydantic import BaseModel, ValidationError

from dendrite.logic.llm.agent import Agent
from dendrite.logic.llm.config import LLMConfig

from .prompts import SEGMENT_PROMPT


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


def parse_segment_output(text: str, index: int) -> SegmentAgentReponseType:
    json_pattern = r"```json(.*?)```"
    res = None

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

            res = SegmentAgentSuccessResponse(
                reason=json_data["reason"],
                status="success",
                d_id=json_data["d_id"],
            )
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to decode JSON: {e}")

    if res is None:
        try:
            res = SegmentAgentFailureResponse.model_validate_json(json_matches[0])
        except ValidationError as e:
            logger.bind(json=json_matches[0]).error(
                f"Failed to parse JSON: {e}",
            )
            res = SegmentAgentFailureResponse(
                reason="Failed to parse JSON", status="failed", index=index
            )

    res.index = index
    return res


async def extract_relevant_d_ids(
    prompt: str, segments: List[str], index: int, llm_config: LLMConfig
) -> SegmentAgentReponseType:
    agent = Agent(llm_config.get("segment_agent"), system_prompt=SEGMENT_PROMPT)
    message = ""
    for segment in segments:
        message += (
            f"""###### SEGMENT ######\n\n{segment}\n\n###### SEGMENT END ######\n\n"""
        )

    message += f"Can you get the d_id of the elements that match the following description:\n\n{prompt} element\n\nIf you've selected an element you should NOT select another element that is a child of the element you've selected. It is important that you follow this."
    message += """\nOutput how you think. Think step by step. if there are multiple candidate elements return all of them. Don't make up d-id for elements if they are not present/don't match the description. Limit your reasoning to 2-3 sentences\nOnly include the json block – don't output an array, only ONE object."""

    max_retries = 3
    for attempt in range(max_retries):
        res = await agent.add_message(message)
        if res is None:
            message = "I didn't receive a response. Please try again."
            continue

        try:
            parsed_res = parse_segment_output(res, index)
            # If we successfully parsed the result, return it
            return parsed_res
        except Exception as e:
            # If we encounter a ValueError, ask the agent to correct its output
            logger.warning(f"Error in segment agent: {e}")
            message = f"An exception occurred in your output: {e}\n\nPlease correct your output and try again. Ensure you're providing a valid JSON response."

    # If we've exhausted all retries, return a failure response
    return SegmentAgentFailureResponse(
        reason="Max retries reached without successful parsing",
        status="failed",
        index=index,
    )
