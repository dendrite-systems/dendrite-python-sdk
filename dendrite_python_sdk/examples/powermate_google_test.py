import asyncio
import os
from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv
from dendrite_python_sdk.exceptions.DendriteException import DendriteException
from dendrite_python_sdk.exceptions.IncorrectOutcomeException import (
    IncorrectOutcomeException,
)
from pydantic import BaseModel

from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.ai_util.generate_text import (
    multiple_expensive_smart_slow_generate_text,
)

load_dotenv(find_dotenv())


class FacebookGroupInfomation(BaseModel):
    name: str | None
    description: str | None
    amount_of_followers: int | None
    is_public: bool
    url: str


all_facebook_info = []


async def run():
    try:
        openai_api_key = os.environ.get("OPENAI_API_KEY", "")

        llm_config = LLMConfig(openai_api_key=openai_api_key)
        dendrite_browser = DendriteBrowser(
            llm_config=llm_config, playwright_options={"headless": False}
        )

        await dendrite_browser.launch()

        languages = ["Swedish", "English", "Estonia"]

        topics = [
            "Tesla",
        ]

        prompts = []
        for language in languages:
            for topic in topics:
                prompts.append(
                    f"We are trying to find facebook communities of EV owners. Please output a concise google search query for facebook groups of the car brand '{topic}' in the language/country '{language}'. Don't output citation marks, only text. Example: 'Teslaägare i sverige facebook' or 'tesla owners facebook'"
                )

        generated_search_queries = await multiple_expensive_smart_slow_generate_text(
            llm_config, prompts
        )

        print("generated_search_queries: ", generated_search_queries)

        group_urls = set()

        for search_query in generated_search_queries:
            search_results = await dendrite_browser.google_search(
                search_query,
                filter_results_prompt="Only list results that are facebook group pages about electric vehicles. They look like this: https://facebook.com/groups/xxx",
            )
            for res in search_results:
                group_urls.add(res.url)

        print("group_urls: ", group_urls)

        for url in list(group_urls):
            page = await dendrite_browser.goto(url, load_entire_page=True)
            try:
                scrape_res: FacebookGroupInfomation = await page.scrape(
                    "You are on a facebook community page, please fetch the information I specified in the model.",
                    pydantic_return_model=FacebookGroupInfomation,
                )
                all_facebook_info.append(scrape_res)
            except DendriteException as e:
                print(f"Failed to {e.message}")

        print("group_urls: ", group_urls)
        await dendrite_browser.close()
    except IncorrectOutcomeException as e:
        print("Incorrect expected outcome! ", e.message)
    except DendriteException as e:
        print(e.message)


asyncio.run(run())


# elbil + facebook group
# elbil + facebook group + bilmärke + land

# grupper och pages, endast grupper
# Landets kod för att filtrera
