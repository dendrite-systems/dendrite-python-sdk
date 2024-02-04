import json
import os
import openai
from dendrite_python_sdk.DendriteAPI import DendriteAPI
from dendrite_python_sdk.openai_tools import go_to_website, scroll, look_at_page
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

openai_api_key = os.environ.get("OPENAI_API_KEY")
dendrite_api_key = os.environ.get("DENDRITE_API_KEY")

custom_action_tool = {
    "type": "function",
    "function": {
        "name": "custom_action",
        "parameters": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "Specify why you are visiting the website. E.g 'I'm visiting the website to fetch the lastest news about the startup Dendrite.'",
                },
            },
            "required": ["data"],
        },
    },
}


def custom_action(data: str):
    # Does something useful here
    res = f"Custom action completed. Data: {data}"
    print(f"\n\n{res}!!")
    return res


def run_agent():
    messages = [
        {"role": "system", "content": "The assistant is a AI agent that completes tasks for the user. It is autonomous and can keep executing actions until the task is completed."},
        {"role": "user", "content": "Please go to to the website https://www.scrapethissite.com/pages/forms/ without vision and scroll down until so you see the entire table, look at the entire table and get the team with the most wins and enter that name into custom_action as the data argument."},
    ]
    max_iterations = 8
    iterations = 0

    openai_client = openai.OpenAI(api_key=openai_api_key)
    dendrite_client = DendriteAPI(api_key=dendrite_api_key)

    actions = [go_to_website, scroll, look_at_page,  custom_action_tool]

    while iterations < max_iterations:
        iterations += 1

        req_args = {
            "model": "gpt-3.5-turbo-1106",
            "messages": messages,
            "max_tokens": 500,
            "tools": actions,
            "tool_choice": "auto"
        }
        response = openai_client.chat.completions.create(**req_args)
        if response.choices[0]:
            dict_res = response.choices[0].message.dict(exclude_none=True)
            messages.append(dict_res)

            tool_calls = response.choices[0].message.tool_calls

            if not tool_calls:
                break
            else:
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    valid_args = {k: v for k, v in function_args.items()
                                  if v is not None}

                    function_response = "No response"

                    if function_name == "go_to_website":
                        function_response = dendrite_client.go_to_website(
                            **valid_args)
                    elif function_name == "scroll":
                        function_response = dendrite_client.scroll(
                            **valid_args)
                    elif function_name == "look_at_page":
                        function_response = dendrite_client.look_at_page(
                            **valid_args)
                    elif function_name == "custom_action":
                        function_response = custom_action(**valid_args)

                    tool_call = {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(function_response),
                    }
                    messages.append(tool_call)
                    print(
                        f"\n\n\n\nMessages:\n{json.dumps(messages, indent=2)}")
        else:
            break
