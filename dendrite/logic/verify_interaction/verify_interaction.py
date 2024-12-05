import json
from typing import List

from bs4 import BeautifulSoup

from dendrite.logic.config import Config
from dendrite.logic.llm.agent import LLM, Agent, Message
from dendrite.models.dto.make_interaction_dto import VerifyActionDTO
from dendrite.models.response.interaction_response import InteractionResponse


async def verify_action(
    make_interaction_dto: VerifyActionDTO, config: Config
) -> InteractionResponse:

    if (
        make_interaction_dto.interaction_type == "fill"
        and make_interaction_dto.value == ""
    ):
        raise Exception(f"Error: You need to specify the keys you want to send.")

    interaction_verb = ""
    if make_interaction_dto.interaction_type == "click":
        interaction_verb = "clicked on"
    elif make_interaction_dto.interaction_type == "fill":
        interaction_verb = "sent keys to"

    locator_desc = ""
    if make_interaction_dto.dendrite_id != "":
        locator_desc = "the dendrite id '{element_dendrite_id}'"

    expected_outcome = (
        ""
        if make_interaction_dto.expected_outcome == None
        else f"The expected outcome is: '{make_interaction_dto.expected_outcome}'"
    )
    prompt = f"I {interaction_verb} a <{make_interaction_dto.tag_name}> element with {locator_desc}. {expected_outcome}"

    messages: List[Message] = [
        {
            "role": "user",
            "content": [],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
                {
                    "type": "text",
                    "text": "Here is the viewport before the interaction:",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{make_interaction_dto.screenshot_before}"
                    },
                },
                {
                    "type": "text",
                    "text": "Here is the viewport after the interaction:",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{make_interaction_dto.screenshot_after}"
                    },
                },
                {
                    "type": "text",
                    "text": """Based of the expected outcome, please output a json object that either confirms that the interaction was successful or that it failed. Output a json object like this with no description or backticks, just valid json. {"status": "success" | "failed", "message": "Give a short description of what happened and if the interaction completed successfully or failed to reach the expected outcome, write max 100 characters."}""",
                },
            ],
        },
    ]

    default = LLM(model="gpt-4o", max_tokens=150)
    llm = Agent(config.llm_config.get("verify_action", default))

    res = await llm.call_llm(messages)
    try:
        dict_res = json.loads(res)
        return InteractionResponse(
            message=dict_res["message"],
            status=dict_res["status"],
        )
    except:
        pass

    raise Exception("Failed to parse interaction page delta.")
