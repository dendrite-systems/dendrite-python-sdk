# dendrite-python-sdk

## Installation:

```
pip install dendrite-python-sdk
```

## Authentication:

Get your API key by going to https://dendrite.se and creating an account.

You must enter your own OpenAI API key into your Dendrite account's environment variables before you can start.

## Complete web tasks with Dendrite's agent:

```python
client = DendriteAPI('your-api-key')

dto = {
    "message": "Please go to https://www.scrapethissite.com/pages/forms/ and scrape all the Team's names.",
    "store_chat":  True

}
res = client.complete_task(dto)

print(res.message) # Description of how the results were acheived
print(res.data) # JSON containing the data from the task if there is any
```

## Complete web tasks with your own agent:

Entire example can be found in /examples.

```python

...Custom actions...


messages = [
    {"role": "system", "content": "The assistant is a AI agent [...] "},
    {"role": "user", "content": "Please go to the website https://scrapethis [...] "},
]
max_iterations = 10
iterations = 0
openai_api_key = os.environ.get("OPENAI_API_KEY")
dendrite_api_key = os.environ.get("DENDRITE_API_KEY")

openai_client = openai.OpenAI(api_key=openai_api_key)
dendrite_client = DendriteAPI(api_key=dendrite_api_key)

actions = [go_to_website, scroll, custom_action_tool]

while iterations < max_iterations:
    iterations += 1

    response = openai_client.chat.completions.create({
        "model": "gpt-3.5-turbo-1106",
        "messages": messages,
        "tools": actions,
    })
    tool_calls = response.tool_calls
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
                function_response = dendrite_client.go_to_website(**valid_args)
            elif function_name == "scroll":
                function_response = dendrite_client.scroll(**valid_args)
            elif function_name == "custom_action":
                function_response = custom_action(**valid_args)

            tool_call = {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            }
            messages.append(tool_call)

```
