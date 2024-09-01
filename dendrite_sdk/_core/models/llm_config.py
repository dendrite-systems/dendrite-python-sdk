from typing import Optional
from pydantic import BaseModel


class LLMConfig(BaseModel):
    openai_api_key: str
    anthropic_api_key: Optional[str] = None
