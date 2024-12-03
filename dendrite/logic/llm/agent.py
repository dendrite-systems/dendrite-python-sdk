import json
from typing import Any, Dict, List, Optional, Union, cast

import litellm
from litellm.files.main import ModelResponse
from loguru import logger
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

Message = ChatCompletionMessageParam


class LLMContextLengthExceededException(Exception):
    CONTEXT_LIMIT_ERRORS = [
        "expected a string with maximum length",
        "maximum context length",
        "context length exceeded",
        "context_length_exceeded",
        "context window full",
        "too many tokens",
        "input is too long",
        "exceeds token limit",
    ]

    def __init__(self, error_message: str):
        self.original_error_message = error_message
        super().__init__(self._get_error_message(error_message))

    def _is_context_limit_error(self, error_message: str) -> bool:
        return any(
            phrase.lower() in error_message.lower()
            for phrase in self.CONTEXT_LIMIT_ERRORS
        )

    def _get_error_message(self, error_message: str):
        return (
            f"LLM context length exceeded. Original error: {error_message}\n"
            "Consider using a smaller input or implementing a text splitting strategy."
        )


LLM_CONTEXT_WINDOW_SIZES = {
    # openai
    "gpt-4": 8192,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "o1-preview": 128000,
    "o1-mini": 128000,
    # deepseek
    "deepseek-chat": 128000,
    # groq
    "gemma2-9b-it": 8192,
    "gemma-7b-it": 8192,
    "llama3-groq-70b-8192-tool-use-preview": 8192,
    "llama3-groq-8b-8192-tool-use-preview": 8192,
    "llama-3.1-70b-versatile": 131072,
    "llama-3.1-8b-instant": 131072,
    "llama-3.2-1b-preview": 8192,
    "llama-3.2-3b-preview": 8192,
    "llama-3.2-11b-text-preview": 8192,
    "llama-3.2-90b-text-preview": 8192,
    "llama3-70b-8192": 8192,
    "llama3-8b-8192": 8192,
    "mixtral-8x7b-32768": 32768,
}


class LLM:
    def __init__(
        self,
        model: str,
        timeout: Optional[Union[float, int]] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        n: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        max_completion_tokens: Optional[int] = None,
        max_tokens: Optional[int] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[int, float]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        seed: Optional[int] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        base_url: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        callbacks: List[Any] = [],
        **kwargs,
    ):
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.top_p = top_p
        self.n = n
        self.stop = stop
        self.max_completion_tokens = max_completion_tokens
        self.max_tokens = max_tokens
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.logit_bias = logit_bias
        self.response_format = response_format
        self.seed = seed
        self.logprobs = logprobs
        self.top_logprobs = top_logprobs
        self.base_url = base_url
        self.api_version = api_version
        self.api_key = api_key
        self.callbacks = callbacks
        self.kwargs = kwargs

        litellm.drop_params = True

    def call(self, messages: Message) -> str:

        try:
            params = {
                "model": self.model,
                "messages": messages,
                "timeout": self.timeout,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "n": self.n,
                "stop": self.stop,
                "max_tokens": self.max_tokens or self.max_completion_tokens,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
                "logit_bias": self.logit_bias,
                "response_format": self.response_format,
                "seed": self.seed,
                "logprobs": self.logprobs,
                "top_logprobs": self.top_logprobs,
                "api_base": self.base_url,
                "api_version": self.api_version,
                "api_key": self.api_key,
                "stream": False,
                **self.kwargs,
            }

            params = {k: v for k, v in params.items() if v is not None}

            response = litellm.completion(**params)
            response = cast(ModelResponse, response)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            if not LLMContextLengthExceededException(str(e))._is_context_limit_error(
                str(e)
            ):
                logger.error(f"LiteLLM call failed: {str(e)}")

            raise  # Re-raise the exception after logging

    async def acall(self, messages: List[Message]) -> ModelResponse:

        try:
            params = {
                "model": self.model,
                "messages": messages,
                "timeout": self.timeout,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "n": self.n,
                "stop": self.stop,
                "max_tokens": self.max_tokens or self.max_completion_tokens,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
                "logit_bias": self.logit_bias,
                "response_format": self.response_format,
                "seed": self.seed,
                "logprobs": self.logprobs,
                "top_logprobs": self.top_logprobs,
                "api_base": self.base_url,
                "api_version": self.api_version,
                "api_key": self.api_key,
                "stream": False,
                **self.kwargs,
            }

            params = {k: v for k, v in params.items() if v is not None}

            response = await litellm.acompletion(**params)
            response = cast(ModelResponse, response)
            return response
        except Exception as e:
            if not LLMContextLengthExceededException(str(e))._is_context_limit_error(
                str(e)
            ):
                logger.error(f"LiteLLM call failed: {str(e)}")

            raise  # Re-raise the exception after logging

    def get_context_window_size(self) -> int:
        return int(LLM_CONTEXT_WINDOW_SIZES.get(self.model, 8192) * 0.75)


class Agent:
    def __init__(
        self,
        model: Union[LLM, str],
        system_prompt: Optional[str] = None,
    ):
        self.messages: List[Message] = (
            [] if not system_prompt else [{"role": "system", "content": system_prompt}]
        )

        if isinstance(model, str):
            self.llm = LLM(model)
        else:
            self.llm = model

    async def add_message(self, message: str) -> str:
        self.messages.append({"role": "user", "content": message})

        text = await self.call_llm(self.messages)

        self.messages.append({"role": "assistant", "content": text})

        return text

    async def call_llm(self, messages: List[Message]) -> str:
        res = await self.llm.acall(messages)

        if len(res.choices) == 0:
            logger.error("No choices outputed: ", res)
            raise Exception("No choices from model")

        choices = cast(List[litellm.Choices], res.choices)
        text = choices[0].message.content

        if text is None:
            logger.error(
                f"No text content in the response | response: {res} ",
            )
            raise Exception("No text content in the response")
        return text
