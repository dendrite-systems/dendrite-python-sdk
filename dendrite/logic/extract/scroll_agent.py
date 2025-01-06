import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal, Optional

from loguru import logger
from openai.types.chat.chat_completion_content_part_param import (
    ChatCompletionContentPartParam,
)

from dendrite.logic.llm.agent import Agent, Message
from dendrite.logic.llm.config import LLMConfig
from dendrite.models.page_information import PageInformation

ScrollActionStatus = Literal["done", "scroll_down", "loading", "error"]


@dataclass
class ScrollResult:
    element_to_inspect_html: List[str]
    segment_index: int
    status: ScrollActionStatus
    message: Optional[str] = None


class ScrollRes(ABC):
    @abstractmethod
    def parse(self, data_dict: dict, segment_i: int) -> Optional[ScrollResult]:
        pass


class ElementPromptsAction(ScrollRes):
    def parse(self, data_dict: dict, segment_i: int) -> Optional[ScrollResult]:
        if "element_to_inspect_html" in data_dict:

            status = (
                "scroll_down"
                if not data_dict.get("continue_scrolling", False)
                else "done"
            )

            return ScrollResult(data_dict["element_to_inspect_html"], segment_i, status)
        return None


class LoadingAction(ScrollRes):
    def parse(self, data_dict: dict, segment_i: int) -> Optional[ScrollResult]:
        if data_dict.get("is_loading", False):
            return ScrollResult([], segment_i, "loading")
        return None


class ErrorRes(ScrollRes):
    def parse(self, data_dict: dict, segment_i: int) -> Optional[ScrollResult]:
        if "error" in data_dict:
            return ScrollResult(
                [],
                segment_i,
                "error",
                data_dict["error"],
            )
        return None


class ScrollAgent(Agent):
    def __init__(self, page_information: PageInformation, llm_config: LLMConfig):
        super().__init__(llm_config.get("scroll_agent"))
        self.page_information = page_information
        self.choices: List[ScrollRes] = [
            ElementPromptsAction(),
            LoadingAction(),
            ErrorRes(),
        ]

        self.logger = logger.bind(agent="scroll_agent")

    async def scroll_through_page(
        self,
        combined_prompt: str,
        image_segments: List[str],
    ) -> ScrollResult:
        messages = [self.create_initial_message(combined_prompt, image_segments[0])]
        all_elements_to_inspect_html = []
        current_segment = 0

        while current_segment < len(image_segments):
            data_dict = await self.process_segment(messages)

            for choice in self.choices:
                result = choice.parse(data_dict, current_segment)
                if result:
                    if result.element_to_inspect_html:
                        all_elements_to_inspect_html.extend(
                            result.element_to_inspect_html
                        )
                    return result

            if "element_to_inspect_html" in data_dict:
                all_elements_to_inspect_html.extend(
                    data_dict["element_to_inspect_html"]
                )

            if self.should_continue_scrolling(
                data_dict, current_segment, len(image_segments)
            ):
                current_segment += 1
                scroll_message = self.create_scroll_message(
                    image_segments[current_segment]
                )
                messages.append(scroll_message)
            else:
                break

        return ScrollResult(all_elements_to_inspect_html, current_segment, "done")

    async def process_segment(self, messages: List[Message]) -> dict:

        text = await self.call_llm(messages)
        messages.append({"role": "assistant", "content": text})

        json_pattern = r"```json(.*?)```"

        json_matches = re.findall(json_pattern, text, re.DOTALL)

        if len(json_matches) > 1:
            logger.warning("Agent output multiple actions in one message")
            error_message = "Error: Please output only one action at a time."
            messages.append({"role": "user", "content": error_message})
            raise Exception(error_message)
        elif json_matches:
            return json.loads(json_matches[0].strip())

        error_message = "No valid JSON found in the response"
        logger.error(error_message)
        messages.append({"role": "user", "content": error_message})
        raise Exception(error_message)

    def create_initial_message(self, combined_prompt: str, first_image: str) -> Message:
        content: List[ChatCompletionContentPartParam] = [
            {
                "type": "text",
                "text": f"""You are a web scraping agent that can code scripts to solve the web scraping tasks listed below for the webpage I'll specify. Before we start coding, we need to inspect the html of the page closer.

This is the web scraping task:
<TASK DESCRIPTION>
{combined_prompt}
</TASK DESCRIPTION>

Analyze the viewport and decide on the next action:

1. Identify elements that we want to inspect closer so we can write the script. Do this by outputting a message with a list of prompts to find the relevant element(s). 

Output as few elements as possible, but it should be enought to gain a proper understanding of the DOM for our script. 

If a list of items need to be extracted, consider getting a few unique examples of items from the list that differ slightly so we can create code that accounts for their differences. Avoid listing several elements that are very similar since we can infer the structure of one or two of them to the rest.

Don't get several different parts of one relevant element, just get the whole element since it's easier to just inspect the whole element. 

Avoid selecting very large elements that contain a lot of html since it can be very overwhelming to inspect.

Always be specific about the element you are thinking of, don't write 'get a item', write 'get the item with the text "Item Name"'.

Here's an example of a good output:
[Short reasoning first, max one paragraph]
```json
{{
    "element_to_inspect_html": ["The small container containing the weekly amount of downloads, labeled 'Weekly Downloads'", "The element containing the main body of article text, the title is 'React Router DOM'."],
    "continue_scrolling": true/false (only scroll down if you think more relevant elements are further down the page, only do this if you need to)
}}
```

2. If you can't see relevant elements just yet, but you think more data might be available further down the page, output:
[Short reasoning first, max one paragraph]
```json
{{
    "scroll_down": true
}}
```

3. This page was first loaded {round(self.page_information.time_since_frame_navigated, 2)} second(s) ago. If the page is blank or the data is not available on the current page it could be because the page is still loading. If you believe this is the case, output:
[Short reasoning first, max one paragraph]
```json
{{
    "is_loading": true
}}
```

4. In case you the data is not available on the current page and the task does not describe how to handle the non-available data, or there seems to be some kind of mistake, output a json with a short error message, like this:
[Short reasoning first, max one paragraph]
```json
{{
    "error": "This page doesn't contain any package data, welcome page for 'dendrite.systems', it won't be possible to code a script to extract the requested data.",
    "was_blocked_by_recaptcha": true/false
}}
```

Continue scrolling and accumulating element prompts until you feel like we have enough elements to inspect to create an excellent script.

Important: Only output one json object per message.

Below is a screenshot of the current page, if it looks blank or empty it could still be loading. If this is the case, don't guess what elements to inspect, respond with is loading.""",
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{first_image}"},
            },
        ]

        msg: Message = {"role": "user", "content": content}
        return msg

    def create_scroll_message(self, image: str) -> Message:
        return {
            "role": "user",
            "content": [
                {"type": "text", "text": "Scrolled down, here is the new viewport:"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image}",
                    },
                },
            ],
        }

    def should_continue_scrolling(
        self, data_dict: dict, current_index: int, total_segments: int
    ) -> bool:
        return (
            "scroll_down" in data_dict or data_dict.get("continue_scrolling", False)
        ) and current_index + 1 < total_segments
