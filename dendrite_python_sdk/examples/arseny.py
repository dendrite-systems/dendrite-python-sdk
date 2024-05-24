import asyncio
import os
from typing import List
from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv
from pydantic import BaseModel
from dendrite_python_sdk.models.LLMConfig import LLMConfig


load_dotenv(find_dotenv())


class StartupInfo(BaseModel):
    Company_name: str
    Country: str
    City: str
    Start_year: str
    Number_of_employees: str
    Funding: str
    Funding_rounds: str
    Number_of_investors: str
    Founders: str
    Website_url: str


class StartupInfoList(BaseModel):
    startups: List[StartupInfo]


start_ups: List[StartupInfo] = []


async def run():
    dendrite_browser = DendriteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", "")
    )

    urls = [
        "https://www.failory.com/startups/energy",
        "https://www.failory.com/startups/renewable-energy",
    ]

    await dendrite_browser.launch()

    for url in urls:
        page = await dendrite_browser.goto(url)
        res: StartupInfoList = await page.scrape(
            "Get all the start up information. Make sure you get each startups URL!",
            pydantic_return_model=StartupInfoList,
        )
        start_ups.extend(res.startups)

    for startup in start_ups:
        print(startup)

    await dendrite_browser.close()


asyncio.run(run())
