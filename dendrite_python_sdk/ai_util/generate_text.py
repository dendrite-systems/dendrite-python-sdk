import asyncio
import json
from typing import Any, List
import backoff  # type: ignore
import logging

from openai.types.chat import ChatCompletion
from openai import AsyncOpenAI, RateLimitError


from dendrite_python_sdk.models.LLMConfig import LLMConfig


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def multiple_expensive_smart_slow_generate_text(
    llm_config_dto: LLMConfig, prompts: List[str], config={}
) -> List[str]:

    tasks = []
    for prompt in prompts:
        tasks.append(expensive_smart_slow_generate_text(llm_config_dto, prompt, config))

    return await asyncio.gather(*tasks)


async def multiple_cheap_fast_dumb_generate_text(
    llm_config_dto: LLMConfig, prompts: List[str], config={}
) -> List[str]:

    tasks = []
    for prompt in prompts:
        tasks.append(cheap_fast_dumb_generate_text(llm_config_dto, prompt, config))

    return await asyncio.gather(*tasks)


async def cheap_fast_dumb_generate_text(
    llm_config_dto: LLMConfig, prompt: str, config={}
) -> str:
    default_config = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "gpt-3.5-turbo",
        **config,
    }
    res = await async_openai_request(default_config, llm_config_dto)
    return str(res.choices[0].message.content)


async def expensive_smart_slow_generate_text(
    llm_config_dto: LLMConfig, prompt: str, config={}
) -> str:
    default_config = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "gpt-4o",
        **config,
    }
    res = await async_openai_request(default_config, llm_config_dto)
    return str(res.choices[0].message.content)


async def async_openai_request(
    request_config, llm_config_dto: LLMConfig, print_messages=False
) -> ChatCompletion:

    @backoff.on_exception(backoff.expo, RateLimitError, max_tries=10, max_time=300)
    async def async_openai_request_retry(
        request_config, print_messages=False
    ) -> ChatCompletion:
        try:
            api_key = llm_config_dto.openai_api_key
            client = AsyncOpenAI(api_key=api_key)

            if print_messages:
                print(
                    "messages sent to API: ",
                    json.dumps(request_config["messages"], indent=2),
                )
            args: dict[str, Any] = {"temperature": 0, **request_config}
            response: ChatCompletion = await client.chat.completions.create(**args)
            return response

        except RateLimitError as e:
            logger.error(f"Rate limit error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    response = await async_openai_request_retry(request_config, print_messages)
    return response
