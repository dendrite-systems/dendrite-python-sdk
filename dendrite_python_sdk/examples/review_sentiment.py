import json
import os
import asyncio
from typing import List

from dendrite_python_sdk import DendriteBrowser
from dendrite_python_sdk.ai_util.generate_text import (
    multiple_cheap_fast_dumb_generate_text,
)
from dotenv import load_dotenv, find_dotenv
from pydantic import BaseModel
import pandas as pd

load_dotenv(find_dotenv())


async def main():
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    dendrite_browser = DendriteBrowser(openai_api_key=openai_api_key)

    # Let's specify some pydantic models for the structure of the reviews
    class Review(BaseModel):
        recommended_the_game: bool
        text: str
        hours_on_record: int

    class ResponseData(BaseModel):
        reviews: List[Review]

    # Go to the game 'Fishards' review page on steam
    page = await dendrite_browser.goto(
        "https://steamcommunity.com/app/1637140/reviews/?browsefilter=toprated&snr=1_5_100010_"
    )

    # Scrape all the reviews
    res: ResponseData = await page.scrape(
        "Get all the reviews in the structure of the model I specified. The text should be a stripped string that contains what the reviewer wrote in their post.",
        pydantic_return_model=ResponseData,
    )

    # Create a list of prompts asking if the reviewer thought the game had bad controls or not enough players online
    prompts = [
        f"""This is a review for the Game Fishards:
{review.text}

Please output a valid json object without any backticks like this:

{{"thought_controls_were_bad": "TRUE" or "FALSE" or "NOT_SPECIFIED", "thought_not_enough_players_online": "TRUE" or "FALSE" or "NOT_SPECIFIED"}}"""
        for review in res.reviews
    ]

    # Make a batch request to OpenAI containing all the prompts to OpenAI with our AI util functions
    generated_results = await multiple_cheap_fast_dumb_generate_text(
        openai_api_key, prompts
    )

    # Merge data from LLM and scraped reviews and put into an excel sheet
    review_data = []
    for generated_result, review in zip(generated_results, res.reviews):
        try:
            generated_result_dict = json.loads(generated_result)
            review_data.append(
                {
                    "recommend_the_game": review.recommended_the_game,
                    "text": review.text,
                    "hours_on_record": review.hours_on_record,
                    "thought_controls_were_bad": generated_result_dict[
                        "thought_controls_were_bad"
                    ],
                    "thought_not_enough_players_online": generated_result_dict[
                        "thought_not_enough_players_online"
                    ],
                }
            )
        except Exception:
            print(f"Failed to parse json from LLM. Output: {generated_result}")

    df = pd.DataFrame(review_data)
    df.to_excel("fishards_reviews.xlsx", index=False)


asyncio.run(main())
