import asyncio
import os
from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv
from dendrite_python_sdk.exceptions.DendriteException import DendriteException
from dendrite_python_sdk.exceptions.IncorrectOutcomeException import (
    IncorrectOutcomeException,
)

from dendrite_python_sdk.models.LLMConfig import LLMConfig

load_dotenv(find_dotenv())

all_companies = {}


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

            res = await page.scrape(
                prompt="Extract the portfolio companies urls, the more info url should be a valid link that I can use to find more information on",
                return_data_json_schema={
                    "type": "array",
                    "items": {
                        "name": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        "more_info_url": {
                            "anyOf": [{"type": "string"}, {"type": "null"}]
                        },
                    },
                },
            )

            print(type(res.json_data))

            for item in list(res.json_data):
                print(item)
                url = item["more_info_url"]
                print("Url; ", url)

            all_companies[url] = res

        print(all_companies)
        await dendrite_browser.close()
    except IncorrectOutcomeException as e:
        print("Incorrect expected outcome! ", e.message)
    except DendriteException as e:
        print(e.message)


asyncio.run(run())
