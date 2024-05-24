import asyncio
import os
from typing import List
from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv
from dendrite_python_sdk.exceptions.DendriteException import DendriteException
from dendrite_python_sdk.exceptions.IncorrectOutcomeException import (
    IncorrectOutcomeException,
)
from pydantic import BaseModel

from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.ai_util.generate_text import (
    multiple_cheap_fast_dumb_generate_text,
)

load_dotenv(find_dotenv())


class ReturnData(BaseModel):
    name: str | None
    description: str | None
    linkedin_page_url: str | None
    more_info_url: str | None
    owned_by_vc: str


class ReturnDataList(BaseModel):
    data: List[ReturnData]


all_companies = []


async def run():
    try:
        openai_api_key = os.environ.get("OPENAI_API_KEY", "")

        llm_config = LLMConfig(openai_api_key=openai_api_key)
        dendrite_browser = DendriteBrowser(
            llm_config=llm_config, playwright_options={"headless": False}
        )

        await dendrite_browser.launch()

        vc_firm_portfolios = [
            "https://cherry.vc/en/founders",
            "https://wave.ventures/#portfolio",
        ]

        for url in vc_firm_portfolios:
            page = await dendrite_browser.goto(url, load_entire_page=True)

            return_data: ReturnDataList = await page.scrape_with_pydantic(
                prompt="Extract the portfolio companies urls, the more info url should be a valid link that I can use to find more information on. '/en/founders/cosuno' isn't valid, you must append the domain of the current website in cases like this! If you can't find all the data for the script it's fine if some fields are null. Don't include '(exit)' or other fragements inside the extracted 'name' parameter. owned_by_vc is the name of the VC that has the company in it's portfolio.",
                pydantic_return_model=ReturnDataList,
            )

            extracted_company_data = return_data.data

            prompts = [
                f"Please generate a google search query that finds the official linkedin page for this company: {company_data.dict()}.  E.g 'Official linkedin page for 'example company', the bio tech startup'."
                for company_data in extracted_company_data
            ]
            search_queries = await multiple_cheap_fast_dumb_generate_text(
                llm_config, prompts
            )
            for search_query, company_data in zip(
                search_queries, extracted_company_data
            ):
                res = await dendrite_browser.google_search(
                    search_query,
                    f"Only list the official LinkedIn page for the company we are searching for.",
                    load_all_results=False,
                )
                if res:
                    print("res: ", res[0].url)
                    company_data.linkedin_page_url = res[0].url

                all_companies.append(company_data)

        await dendrite_browser.close()
    except IncorrectOutcomeException as e:
        print("Incorrect expected outcome! ", e.message)
    except DendriteException as e:
        print(e.message)


asyncio.run(run())
