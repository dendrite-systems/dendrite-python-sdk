import os
import asyncio
import time
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from dendrite_python_sdk import DendriteRemoteBrowser
from dotenv import load_dotenv, find_dotenv
from dendrite_python_sdk.dto.ScrapePageDTO import ScrapePageDTO

from dendrite_python_sdk.models.PageInformation import PageInformation
from dendrite_python_sdk.ai_util.generate_text import async_openai_request
from dendrite_python_sdk.ai_util.response_extract import extract_json
from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage
from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.request_handler import scrape_page

load_dotenv(find_dotenv())


class EcommerceRequest(BaseModel):
    url: str


# This may include things like price, tax, shipping cost, shipping options (e.g. Amazon prime, 3day shipping), product variants (size with options S, M, L or color with options blue, red, white), etc.


class PriceData(BaseModel):
    price: str = Field(..., description="Include the currency inside the response.")
    currency: str = Field(..., description="e.g USD")
    currencyRaw: str = Field(..., description="e.g $")


class ProductData(BaseModel):
    product_name: str
    # product_description: str = Field(
    #     ...,
    #     description="Get any text that describes the product. Often time this is under 'about product' or similar. Normally at least a paragraph long.",
    # )
    product_image_urls: list[str] = Field(
        ...,
        description="Make sure you get the images you get the large display images and not any smaller ones. They are usually front and center next to the title.",
    )
    shipping_details: Optional[str] = Field(
        ...,
        description="Please list all information regarding shipping cost, shipping options (e.g. Amazon prime, 3day shipping) if available on the page.",
    )

    # original_price: str = Field(
    #     ..., description="Include the currency inside the response."
    # )
    priceData: PriceData
    availability: Optional[bool] = Field(..., description="Is the item in stock or not")
    # available_colors: list[str] = Field(
    #     ...,
    #     description="Please list the colors that are available for this product if applicable.",
    # )
    available_sizes: Optional[list[str]] = Field(
        [],
        description="Get all the available sizes that are selectable on the product page as a list of strings. This value is usually only relevant for clothing items. Sometimes these are found inside size dropdowns. I only want the sizes that are currently available, often times unavailable sizes are greyed out or similar. It's important that you only get the currently available sizes that aren't hidden.",
    )
    # unavailable_sizes: list[str] = Field(
    #     [],
    #     description="Get all the unavailable sizes as a list of strings. I only want the sizes that are currently unavailable, often times unavailable sizes are greyed out or similar.",
    # )


class EcommerceResponse(BaseModel):
    variants: List[ProductData]


async def extract_data(
    page: DendritePage,
    propery_name: str,
    propery_schema: Any,
):
    llm_config = LLMConfig(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )

    print(f"Getting from active_page: {page} name: {propery_name}")

    db_prompt = f"Please extract the data with the following json schema: {propery_schema}. Create a script should return a value that matches the json schemas `type`."
    raw_html = await page.get_content()
    page_info = PageInformation(
        url=page.url,
        raw_html=raw_html,
        interactable_element_info={},
        screenshot_base64="screenshot",
    )

    async def create_script(prompt: str, force_use_cache: bool = False):
        scrape_dto = ScrapePageDTO(
            page_information=page_info,
            llm_config=llm_config,
            prompt=prompt,
            db_prompt=db_prompt,
            expected_return_data=None,
            return_data_json_schema=propery_schema,
            force_use_cache=force_use_cache,
        )

        res = await scrape_page(scrape_dto)
        # print("create_script res: ", res)
        return res

    try:
        res = await create_script(db_prompt, force_use_cache=True)
        print("res: ", res)
        if res.status != "failed":
            print(f" ✅ Used cached script! {res}")
            return res
        else:
            print(" ❌ Need to create a new script.")
    except Exception as e:
        pass

    page_info = await page.get_page_information()
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""Hi! I want you to help me extract e-commerce data.

Requested value to extract: {propery_schema}

Please look at the page and output one of the following:

- Output {{"reasoning": "...", "type": "BAD_SCREENSHOT"}} if the screenshot didn't render correctly.
- Output {{"reasoning": "...", "type": "NOT_AVAILABLE"}} if the information is completely missing from the webpage.
- Output {{"reasoning": "...", "type": "INTERACTION_REQUIRED"}} if you need to click or interact with the website to reveal the relevant information.
- Output {{"reasoning": "...", "type": "SCRAPING_REQUIRED"}} if you need to create a script to scrape the required information from the HTML. This is relevant for extracting e.g image URLs since you cannot know them without scraping.
- Output {{"reasoning": "...", "type": "DATA_VISIBLE", "expected_value": "..."}} if you can see the required data clearly on the page. 'data' should match the expected output value.

Output the json with tripple backticks like in this example:

```json
{{"reasoning": "By looking at the page I can see that the price is clearly visible on the page and equals '100 USD'. It can be found right under the title of the product 'Epic Shoe 10'.", "type": "DATA_AVAILABLE", "expected_value": 100}}
```

`expected_value` should be a real value on the page. If the value is very long (e.g a long body of text) you may output a truncated version.

In `reasoning`, output neighboring text to narrow down the search.

Output the json, starting with `reasoning`, and nothing else. Here is a screenshot of the website:""",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{page_info.screenshot_base64}"
                    },
                },
            ],
        },
    ]

    config = {
        "messages": messages,
        "model": "gpt-4o",
        "temperature": 0,
        "max_tokens": 1500,
    }
    res = await async_openai_request(config, llm_config)

    response_message = res.choices[0].message.content
    if response_message:
        try:
            json_res = extract_json(response_message)
        except Exception as e:
            print("Error parsing: ", response_message)
            return propery_name, response_message

        if json_res["type"] == "DATA_VISIBLE":
            prompt = f"Please extract the data from with this json schema: {propery_schema}. {json_res['reasoning']} So, the expected output from extraction script should be: \n\n{json_res['expected_value']}\n\nCreate a script that can get this value. Don't hardcode the expected outcome into the script, just make sure that the outcome matches it. (Doesn't need to be exactly the same, but similar.)"
            res = await create_script(prompt)
            print(f"Need to create script... '{db_prompt}', res {res}")
            return propery_name, res.json_data
        elif json_res["type"] == "SCRAPING_REQUIRED":
            res = await create_script(db_prompt)
            print(f"Need to create script... '{db_prompt}', res {res}")
            return propery_name, res.json_data
        elif json_res["type"] == "NOT_AVAILABLE":
            if "null" in propery_schema["type"]:
                return propery_name, None
            prompt = f"We are trying to extract the data that follows this JSON schema: {propery_schema}. This data doesn't seem to be available on the page however, so please code a short script that returns a value that matches the schema but returns a value like -1 or 'Not available'."
            print(f"Need to create script... '{db_prompt}', res {res}")
            res = await create_script(prompt)
            return propery_name, res.json_data
        else:
            return propery_name, None

    return propery_name, response_message


# Train Agent (url) use_cache=False, for sample of URLs
# go to page
# see if there are variants, find selector (check visually), iterate over selector pressing each one, see if expected worked or not.
# for each page scrape the requested values from correct place


async def get_all_product_variants(
    page: DendritePage, browser: DendriteRemoteBrowser, use_cache: bool = True
) -> List[Any]:
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    llm_config = LLMConfig(openai_api_key=openai_api_key)
    db_prompt = f"Get the product variants from the page."

    if use_cache:
        # Check if variants cached
        try:
            start_time = time.time()
            variant_buttons = await page.get_interactions_selector(
                prompt=db_prompt, db_prompt=db_prompt, force_use_cache=True
            )
            print("get cache time: ", time.time() - start_time)
            if len(variant_buttons) > 0:
                print("found cached selector!!! ", variant_buttons)

                product_variant_data = []
                for el in variant_buttons[:1]:
                    try:
                        await el.get_playwright_locator().click(timeout=0)

                        active_page = await browser.get_active_page()
                        res = await extract_all(
                            active_page,
                            json_schema=ProductData.model_json_schema(),
                        )
                        print(f"Clicked and got res: {res}.")
                        product_variant_data.append(res)
                    except Exception as e:
                        pass
                return product_variant_data
        except:
            pass

    print("Could not find cached variants selector, going to find them.")
    start_time = time.time()
    page_info = await page.get_page_information()
    print("get page info: ", time.time() - start_time)

    entire_prompt = f"""Hi, we are trying to extract product data from a webpage. Can you help me see if there are any variant of this product displayed on the page? Often times these are color variants, but it could be theme too or something else.

Please look at the page and output one of the following:

- Output {{"reasoning": "...", "type": "VARIANTS_AVAILABLE", "interaction_prompt": "..."}} if there are some kind of variant of the same product you are looking at now. 'interaction_prompt' is a prompt that will be sent to an AI agent that has the task of fetching the relevant variant selection elements. 
- Output {{"reasoning": "...", "type": "NOT_AVAILABLE"}} if there are no variants, or only one variant.

Output the json with tripple backticks like in this example:

```json
{{"reasoning": "Underneath the price three product color variants are visible. They are buttons in a row with small product previews. The current color is 'snow white', the two other colors are 'fire red', 'ocean blue'.", "type": "VARIANTS_AVAILABLE", "interaction_prompt": "Please find the buttons responsible for selecting the different product variants. They are buttons in a row with small product preview images with the colors 'snow white', 'fire red', 'ocean blue'. They are underneath the text 'mega pc gamer 100€' and above the 'chose size' text."}}
```

Output the json, starting with reasoning, and nothing else. Make sure you use texts from the website to anchor the position of the relevant element. Write 200-500 chars per parameter. Here is a screenshot of the website:"""

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": entire_prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{page_info.screenshot_base64}"
                    },
                },
            ],
        },
    ]
    print("entire_prompt for fetching variants: ", entire_prompt)

    config = {
        "messages": messages,
        "model": "gpt-4o",
        "temperature": 0,
        "max_tokens": 1500,
    }
    res = await async_openai_request(config, llm_config)

    response_message = res.choices[0].message.content
    print("response_message: ", response_message)
    if response_message:
        try:
            json_res = extract_json(response_message)
        except Exception as e:
            raise Exception(f"Error parsing: {e}: ", response_message)

        if json_res["type"] == "VARIANTS_AVAILABLE":
            variant_buttons = await page.get_interactions_selector(
                json_res["interaction_prompt"], db_prompt=db_prompt
            )

            results = []
            for el in variant_buttons:
                try:
                    await el.get_playwright_locator().click(timeout=0)
                    active_page = await browser.get_active_page()
                    res = await extract_all(
                        active_page,
                        json_schema=ProductData.model_json_schema(),
                    )
                    results.append(res)
                except Exception as e:
                    pass
            return results
        elif json_res["type"] == "NOT_AVAILABLE":
            active_page = await browser.get_active_page()
            res = await extract_all(
                active_page,
                json_schema=ProductData.model_json_schema(),
            )
            return [res]

    raise Exception("Failed to parse OpenAI message.")


async def extract_all(page: DendritePage, json_schema: Any):
    tasks = []
    for propery_name, propery_schema in json_schema["properties"].items():
        tasks.append(
            extract_data(
                page,
                propery_name,
                propery_schema,
            )
        )

    results = await asyncio.gather(*tasks)
    response_data = {}
    for res in results:
        response_data[res[0]] = res[1]

    print("response_data: ", response_data)
    return response_data


async def extract_product_data(url: str) -> EcommerceResponse:
    dendrite_browser = DendriteRemoteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        dendrite_api_key=os.environ.get("DENDRITE_API_KEY", ""),
    )
    print(" launch: ", url)

    await dendrite_browser.launch()
    page = await dendrite_browser.goto(url, scroll_through_entire_page=False)

    product_variant_data = await get_all_product_variants(page, dendrite_browser)
    print("Found this many variants: ", len(product_variant_data))

    print("page_data_results: ", product_variant_data)

    return EcommerceResponse(variants=product_variant_data)


async def test(url: str):
    browser = DendriteRemoteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        dendrite_api_key=os.environ.get("DENDRITE_API_KEY", ""),
    )
    page = await browser.goto(url, scroll_through_entire_page=False)
    res = await page.scrape(
        "Get the price of the product please",
        use_cache=False,
    )
    print("res: ", res)


asyncio.run(
    extract_product_data(
        "https://www.amazon.com/Lee-Womens-Legendary-Flare-Elevated/dp/B0C5ND84XC/ref=sr_1_16?crid=1IHX3N9NJ72X4&dib=eyJ2IjoiMSJ9.avM_Q9qy2Wbfhz4g7QXlARtkJ-FKfioLrvdK0DKWbqQmVhUPdkDVBEWczNtc9KWpzzzXwckXNkJtm3Xx_NjD2Uu-0obpGkn3o2IIE_fYdc8nDbBv76GyuZHwRt_l6YmZ-3DLCCqvIAno7xa4SOpTL5ApLyrycKygMzS2HZDiKNJbkFJI7gn1VwcK_w-B6roC-PigJpWN0l9ydAvjv3xI4tvFDsQ4mPrFjDUy_7spzBGsTI4YoiBK7xALV4NvXmtMQJzW9NeA95blDRA4tc0E0SmyOp5Ve2OTXCTzNTo_yYQ.-Nmd_HDhA95UDzaYOYZ50GfNgxJUayKfCQRUORtgG3s&dib_tag=se&keywords=jeans+for+women&qid=1719500499&sprefix=jeans%2Caps%2C245&sr=8-16"
        # "https://www.amazon.com/Redragon-S101-Keyboard-Ergonomic-Programmable/dp/B00NLZUM36/ref=sr_1_3?_encoding=UTF8&content-id=amzn1.sym.12129333-2117-4490-9c17-6d31baf0582a&dib=eyJ2IjoiMSJ9.xPISJOYMxoc_9dHbx858fxwpXnhNZrtv8JW5ZP3BaCjqaHIK38QAFzAsY9vAczkOx_jT47M5saeEynDwm1y20BOqIUbVycKgrgWhsv3MCsvpEd57g5uZRNzYwHS9Aw2obI3MPmxewiD3kqCeZDfRh69TGNH_g8luFs-XZxYXIBD2JVQ9pYTQA6VM4k06p7kUjdUQzbe1NHHkPD6bd_mILwz7PFE_rYcpXnDqkLtMtSY.LORYuOmHcSqhnVbbYz8QsC5kxdeESOXcjd_PCPjpzMs&dib_tag=se&keywords=gaming%2Bkeyboard&pd_rd_r=64dc3a90-64a6-40b9-b7a1-2d68d3ecc3b4&pd_rd_w=x25KJ&pd_rd_wg=OZzqF&pf_rd_p=12129333-2117-4490-9c17-6d31baf0582a&pf_rd_r=HP8K759Y8NJCW8Z9C275&qid=1719487385&sr=8-3&th=1"
        # "https://www.amazon.com/Portable-Mechanical-Keyboard-MageGee-Backlit/dp/B098LG3N6R/ref=sr_1_2?_encoding=UTF8&content-id=amzn1.sym.12129333-2117-4490-9c17-6d31baf0582a&dib=eyJ2IjoiMSJ9.xPISJOYMxoc_9dHbx858fxwpXnhNZrtv8JW5ZP3BaCjqaHIK38QAFzAsY9vAczkOx_jT47M5saeEynDwm1y20JZ85TVB8YZ7cwvsm0LDrBK1PUvuJ-xGXkNcVHVIhrQc9kBmR5169dJ6bjz3i9LTKih1i1gw9zMA5shlsZn0KaVLU1EJAlCk2vS5bmQ5Idk0jdUQzbe1NHHkPD6bd_mIL2J7EUeyr51zzG5sIHNZF8s.0rZvfrTY0gQfCCR3e3ZG37IngUeL9TvLAKFP0uxXQm8&dib_tag=se&keywords=gaming%2Bkeyboard&pd_rd_r=a3b11a83-7bdf-42ad-8ccc-850a2a9be0ae&pd_rd_w=thyAn&pd_rd_wg=QuR3V&pf_rd_p=12129333-2117-4490-9c17-6d31baf0582a&pf_rd_r=EGJ9WE3PH43XY2VRNXYS&qid=1719385097&sr=8-2&th=1"
    )
)

# Session ID "get product data variants" + domain to create key  - get ID after run

# Learn:
# 1. Click all variants (expected value check)
# 2. Scrape the relevant data from each one
# 3. Aggrigate generated code


# Run:
# Interact Click all the product variants
# Create interaction script


# Find element - look at page
# Inspect html
# Confirm

# Today:
# Store variant locator (what if different ones?) and get instantly
# Cache extraction scripts
# Set up endpoint
# Nice endpoint: id give train sample -> test sample -> run
