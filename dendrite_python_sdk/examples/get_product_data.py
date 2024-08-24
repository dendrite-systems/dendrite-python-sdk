import os
import asyncio
import time
from typing import List, Optional
import pandas as pd
from pydantic import BaseModel, Field

from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv

from dendrite_python_sdk.dendrite_browser.DendriteRemoteBrowser import DendriteRemoteBrowser

load_dotenv(find_dotenv())


class PriceModel(BaseModel):
    images_url: List[str]
    price: str = Field(..., description="Make sure that the price is clean and contains plain text")
    title: str

async def scrape_price(product_url: str) -> Optional[str]:
    dendrite_browser = DendriteRemoteBrowser(
        dendrite_api_key=os.environ.get("DENDRITE_API_KEY", ""),
        openai_api_key=os.environ.get("OPENAI_API_KEY", "")
    )
    
    time_before = time.time()
    page = await dendrite_browser.goto(
        product_url, scroll_through_entire_page=False
    )
    print("Time to load page: ", time.time() - time_before)


    # Scraping data is as easy as writing a good prompt
    # await page.scroll_through_entire_page()
    price = await page.scrape(
        """Extract the price of the main product on the page, make sure that the extracted value is plain text. Extract the title.
            include the the urls to the product images. There are often two versions of the images, be sure to select the ones that are of the highest quality.""",
        pydantic_return_model=PriceModel
    )
    return price

async def successful_scrape(product_url):
    price = await scrape_price(product_url)
    if price:
        return {'success': True, 'price': price}
    else:
        return {'success': False, 'price': None}


async def main(product_url: str):

    price = await scrape_price(product_url)
    print(price)


    # df = pd.read_csv("products.csv")
    # start = time.time()
    # dendrite_browser = DendriteRemoteBrowser(
    #     dendrite_api_key=os.environ.get("DENDRITE_API_KEY", ""),
    #     openai_api_key=os.environ.get("OPENAI_API_KEY", "")
    # )

    # for url in df["Url"]:
    #     page_start = time.time()
    #     page = await dendrite_browser.goto(
    #         url, scroll_through_entire_page=False
    #     )
    #     price = await page.scrape(
    #         "Exstract the price of the main product on the page, make sure that the extracted value is plain text",
    #         pydantic_return_model=PriceModel
    #     )
    #     print("Time to load page: ", time.time() - page_start)
    #     print(price)
    
    # print("Time to load all pages: ", time.time() - start)

    return
    # # Create a list of tasks
    tasks = [successful_scrape(value) for value in df["Url"]]

    # Run the tasks in parallel and gather results
    results = await asyncio.gather(*tasks)

    # Extract success and price values from results
    success_results = [result['success'] for result in results]
    prices = [result['price'] for result in results]

    # Update the DataFrame
    df["success"] = success_results
    df["price"] = prices

    # Save the updated DataFrame to a new CSV file
    df.to_csv("products_processed.csv", index=False)
        
        
async def scrape_one_browser(browser: DendriteBrowser, product_url: str):
    page = await browser.goto(
        product_url, scroll_through_entire_page=False
    )
    price = await page.scrape(
        
        "Extract the price of the main product on the page, make sure that the extracted value is plain text",
        pydantic_return_model=PriceModel
    )
    return price


asyncio.run(main("https://www.bauhaus.se/vedklyv-scheppach-hl760ls-7t-2200w"))
#https://www.nike.com/se/en/t/academy-dri-fit-football-pants-x1t8FS/DV9736-010
#"https://www.nike.com/se/en/t/sportswear-club-t-shirt-VmJw4S"
# https://www.nike.com/se/en/t/pegasus-41-blueprint-older-road-running-shoes-pz105x/FN5041-103
# https://www.nike.com/se/en/t/pegasus-41-blueprint-older-road-running-shoes-pz105x/FN5041-100
