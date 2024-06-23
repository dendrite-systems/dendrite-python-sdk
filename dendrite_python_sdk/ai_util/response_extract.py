import json
import re


def extract_json(llm_response: str) -> dict:
    json_pattern = r"```json(.*?)```"
    json_matches = re.findall(json_pattern, llm_response, re.DOTALL)

    try:
        for json_match in json_matches:
            extracted_json = json_match.strip()
            data_dict = json.loads(extracted_json)
            return data_dict
        raise Exception("Invalid output from OpenAI")
    except:
        raise Exception("Failed to parse JSON when extracting response")


def extract_python(llm_response: str) -> str:
    code_pattern = r"```python(.*?)```"
    script_matches = re.findall(code_pattern, llm_response, re.DOTALL)

    for script_match in script_matches:
        generated_script = script_match.strip()
        return generated_script
    raise Exception("No code could be extracted from the message.")
