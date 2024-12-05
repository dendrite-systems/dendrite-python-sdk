import re
from typing import List

import json_repair
from jsonschema import validate
from openai.types.chat.chat_completion_content_part_param import (
    ChatCompletionContentPartParam,
)

from dendrite.logic.config import Config
from dendrite.logic.llm.agent import Agent, Message
from dendrite.models.dto.ask_page_dto import AskPageDTO
from dendrite.models.response.ask_page_response import AskPageResponse

from .image import segment_image


async def ask_page_action(ask_page_dto: AskPageDTO, config: Config) -> AskPageResponse:
    image_segments = segment_image(
        ask_page_dto.page_information.screenshot_base64, segment_height=2000
    )

    agent = Agent(config.llm_config.get("ask_page_agent"))
    scrolled_to_segment_i = 0
    content = generate_ask_page_prompt(ask_page_dto, image_segments)
    messages: List[Message] = [
        {"role": "user", "content": content},
    ]

    max_iterations = len(image_segments) + 5
    iteration = 0
    while iteration < max_iterations:
        iteration += 1

        text = await agent.call_llm(messages)
        messages.append(
            {
                "role": "assistant",
                "content": text,
            }
        )

        json_pattern = r"```json(.*?)```"

        if not text:
            continue

        json_matches = re.findall(json_pattern, text, re.DOTALL)

        if len(json_matches) == 0:
            continue

        extracted_json = json_matches[0].strip()
        data_dict = json_repair.loads(extracted_json)

        if not isinstance(data_dict, dict):
            content = "Your message doesn't contain a correctly formatted json object, try again."
            messages.append({"role": "user", "content": content})
            continue

        if "scroll_down" in data_dict:
            next = scrolled_to_segment_i + 1
            if next < len(image_segments):
                content = generate_scroll_prompt(image_segments, next)
            else:
                content = "You cannot scroll any further."
            messages.append({"role": "user", "content": content})
            continue

        elif "return_data" in data_dict and "description" in data_dict:
            return_data = data_dict["return_data"]
            try:
                if ask_page_dto.return_schema:
                    validate(instance=return_data, schema=ask_page_dto.return_schema)
            except Exception as e:
                err_message = "Your return data doesn't match the requested return json schema, try again. Exception: {e}"
                messages.append(
                    {
                        "role": "user",
                        "content": err_message,
                    }
                )
                continue

            return AskPageResponse(
                status="success",
                return_data=data_dict["return_data"],
                description=data_dict["description"],
            )

        elif "error" in data_dict:
            was_blocked = data_dict.get("was_blocked_by_recaptcha", False)
            return AskPageResponse(
                status="error",
                return_data=data_dict["error"],
                description=f'{data_dict["error"]}, was_blocked_by_recaptcha: {was_blocked}',
            )

        else:
            err_message = (
                "Your message doesn't contain a correctly formatted action, try again."
            )
            messages.append(
                {
                    "role": "user",
                    "content": err_message,
                }
            )

    return AskPageResponse(
        status="error",
        return_data="Scrolled through the entire page without finding the requested data.",
        description="",
    )


def generate_ask_page_prompt(
    ask_page_dto: AskPageDTO, image_segments: list, scrolled_to_segment_i: int = 0
) -> List[ChatCompletionContentPartParam]:
    # Generate scroll down hint based on number of segments
    scroll_down_hint = (
        ""
        if len(image_segments) == 1
        else """
    
If you think need to scroll further down, output an object with the key scroll down and nothing else:

Action Message:
[Short reasoning first]
```json
{
    "scroll_down": true
}
```

You can keep scrolling down, noting important details, until you are ready to return the requested data, which you would do in a separate message."""
    )

    # Get return schema prompt
    return_schema_prompt = (
        str(ask_page_dto.return_schema)
        if ask_page_dto.return_schema
        else "No schema specified by the user"
    )

    # Construct the main prompt content
    content: List[ChatCompletionContentPartParam] = [
        {
            "type": "text",
            "text": f"""Please look at the page and return data that matches the requested schema and prompt.

<TASK DESCRIPTION>
{ask_page_dto.prompt}
</TASK DESCRIPTION>

<RETURN JSON SCHEMA>
{return_schema_prompt}
</RETURN JSON SCHEMA>

Look the viewport and decide on the next action:

If you can solve the prompt and return the requested data from the viewport, output a message with tripple backticks and 'json' like in the example below. Make sure `return_data` matches the requested return schema:

Action Message:
[Short reasoning first]
```json
{{
    "description": "E.g There is a red button with the text 'get started' positoned underneath the title 'welcome!'",
    "return_data": {{"element_exists": true, "foo": "bar"}},
}}
```

Remember, `return_data` should be json that matches the structure of the requested json schema if available. Don't forget to include a description.{scroll_down_hint}

In case you think the data is not available on the current page and the task does not describe how to handle the non-available data, or the page is blocked by a captcha puzzle or similar, output a json with a short error message, like this:

Action Message:
[Short reasoning first.]
```json
{{
    "error": "reason why the task cannot be completed here",
    "was_blocked_by_recaptcha": true/false
}}
```

Here is a screenshot of the viewport:""",
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_segments[scrolled_to_segment_i]}"
            },
        },
    ]

    return content


def generate_scroll_prompt(
    image_segments: list, next_segment: int
) -> List[ChatCompletionContentPartParam]:
    """
    Generates the prompt for scrolling to next segment.

    Args:
        image_segments: List of image segments
        next_segment: Index of next segment

    Returns:
        List of message content blocks
    """
    last_segment_reminder = (
        " You won't be able to scroll further now."
        if next_segment == len(image_segments) - 1
        else ""
    )

    content = [
        {
            "type": "text",
            "text": f"""You have scrolled down. You are viewing segment {next_segment+1}/{len(image_segments)}.{last_segment_reminder} Here is the new viewport:""",
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_segments[next_segment]}"
            },
        },
    ]

    return content
