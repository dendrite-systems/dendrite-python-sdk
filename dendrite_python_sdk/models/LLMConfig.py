from pydantic import BaseModel


class LLMConfig(BaseModel):
    openai_api_key: str
