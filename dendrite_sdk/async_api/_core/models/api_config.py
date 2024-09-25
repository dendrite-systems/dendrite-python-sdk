from typing import Optional
from pydantic import BaseModel, model_validator


class APIConfig(BaseModel):
    """
    Configuration model for API keys used in the Dendrite SDK.

    Attributes:
        dendrite_api_key (Optional[str]): The API key for Dendrite services.
        openai_api_key (Optional[str]): The API key for OpenAI services. If you wish to use your own API key, you can do so by passing it to the AsyncDendriteBrowser.
        anthropic_api_key (Optional[str]): The API key for Anthropic services. If you wish to use your own API key, you can do so by passing it to the AsyncDendriteBrowser.

    Raises:
        ValueError: If a valid dendrite_api_key is not provided.
    """

    dendrite_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    @model_validator(mode="before")
    def _check_api_keys(cls, values):
        dendrite_api_key = values.get("dendrite_api_key")

        if not dendrite_api_key:
            raise ValueError(
                "A valid dendrite_api_key must be provided. Make sure you have set the DENDRITE_API_KEY environment variable or passed it to the AsyncDendriteBrowser."
            )

        return values
