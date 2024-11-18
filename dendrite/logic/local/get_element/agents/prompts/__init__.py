def load_prompt(prompt_path: str) -> str:
    with open(prompt_path, "r") as f:
        prompt = f.read()
    return prompt


SEGMENT_PROMPT = load_prompt(
    "dendrite_server_merge/core/web_scraping_agent/get_interactable/agents/prompts/segment.prompt"
)
SELECT_PROMPT = load_prompt(
    "dendrite_server_merge/core/web_scraping_agent/get_interactable/agents/prompts/select.prompt"
)
