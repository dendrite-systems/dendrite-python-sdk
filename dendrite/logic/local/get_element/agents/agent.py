from abc import ABC, abstractmethod
import json
from typing import Any, Dict, Generic, List, Literal, Optional, Type, TypeVar

from anthropic.types import Message, TextBlock

from dendrite_server_merge.core.llm.claude import async_claude_request
from dendrite_server_merge.core.llm.gemini import async_gemini_request
from dendrite_server_merge.core.llm.openai import async_openai_request
from dendrite_server_merge.models.APIConfig import APIConfig


T = TypeVar("T")
U = TypeVar("U")


class Agent(ABC, Generic[T, U]):
    def __init__(
        self,
        model: U,
        api_config: APIConfig,
        system_message: Optional[str] = None,
        temperature: float = 0,
        max_tokens: int = 1500,
    ):
        self.messages: List[Dict] = []
        self.api_config = api_config
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        if system_message:
            self._add_system_message(system_message)

    @abstractmethod
    def _add_system_message(self, message: str) -> None:
        pass

    @abstractmethod
    async def add_message(self, message: str) -> T:
        pass


class AnthropicAgent(
    Agent[Message, Literal["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]]
):
    def __init__(
        self,
        model: Literal["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
        api_config: APIConfig,
        system_message: Optional[str] = None,
        temperature: float = 0,
        max_tokens: int = 1500,
        enable_caching: bool = False,  # Add enable_caching option
    ):
        self.enable_caching = enable_caching  # Store the caching preference
        super().__init__(model, api_config, system_message, temperature, max_tokens)

    def _add_system_message(self, message: str) -> None:
        self.system_msg: List[dict] = [{"type": "text", "text": message}]
        if self.enable_caching:
            self.system_msg[0]["cache_control"] = {"type": "ephemeral"}

    async def add_message(self, message: str) -> Message:
        self.messages.append({"role": "user", "content": message})

        spec = {
            "messages": self.messages,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        if self.system_msg:
            spec["system"] = self.system_msg

        res = await async_claude_request(
            spec, self.api_config, enable_caching=self.enable_caching
        )

        if isinstance(res.content[0], TextBlock):
            self.messages.append({"role": "assistant", "content": res.content[0].text})
        else:
            raise ValueError("Unexpected response type: ", type(res.content[0]))

        return res

    def dump_messages(self) -> str:
        return json.dumps(
            [{"role": "system", "content": self.system_msg}] + self.messages, indent=2
        )


class OpenAIAgent(
    Agent[ChatCompletion, Literal["gpt-3.5", "gpt-4", "gpt-4o", "gpt-4o-mini"]]
):

    def _add_system_message(self, message: str):
        self.messages.append({"role": "system", "content": message})

    async def add_message(self, message: str) -> ChatCompletion:
        self.messages.append({"role": "user", "content": message})

        spec = {
            "messages": self.messages,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        res = await async_openai_request(spec, self.api_config)
        self.messages.append(
            {"role": "assistant", "content": res.choices[0].message.content}
        )
        return res

    def dump_messages(self) -> str:
        return json.dumps(self.messages, indent=2)


class GoogleAgent(Agent[AsyncGenerateContentResponse, str]):

    def _add_system_message(self, message: str):
        self.system_message = message

    async def add_message(self, message: str) -> AsyncGenerateContentResponse:
        self.messages.append({"role": "user", "parts": message})

        res = await async_gemini_request(
            system_message=self.system_message,
            llm_config_dto=self.api_config,
            model_name="gemini-1.5-flash",
            contents=self.messages,
        )

        res.candidates[0].content.parts[0]
        self.messages.append(
            {"role": "assistant", "parts": res.candidates[0].content.parts}
        )

        return res

    def dump_messages(self) -> str:
        return json.dumps(
            [{"role": "system", "parts": "system_message"}] + self.messages, indent=2
        )