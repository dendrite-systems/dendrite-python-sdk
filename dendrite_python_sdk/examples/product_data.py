import os
import asyncio
from typing import Any, List
from pydantic import BaseModel, Field

from dendrite_python_sdk import DendriteRemoteBrowser
from dotenv import load_dotenv, find_dotenv
from dendrite_python_sdk.dto.ScrapePageDTO import ScrapePageDTO

from dendrite_python_sdk.models.PageInformation import PageInformation
from dendrite_python_sdk.ai_util.generate_text import async_openai_request
from dendrite_python_sdk.ai_util.response_extract import extract_json
from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage
from dendrite_python_sdk.models.LLMConfig import LLMConfig
from dendrite_python_sdk.request_handler import get_interactions_selector, scrape_page

load_dotenv(find_dotenv())


class EcommerceRequest(BaseModel):
    url: str


# This may include things like price, tax, shipping cost, shipping options (e.g. Amazon prime, 3day shipping), product variants (size with options S, M, L or color with options blue, red, white), etc.


class ProductData(BaseModel):
    product_name: str
    product_description: str = Field(
        ...,
        description="Get any text that describes the product. Often time this is under 'about product' or similar. Normally at least a paragraph long.",
    )
    product_image_urls: list[str] = Field(
        ...,
        description="Make sure you get the images you get the large display images and not any smaller ones.",
    )
    # shipping_details: str = Field(
    #     ...,
    #     description="Please list all information regarding shipping cost, shipping options (e.g. Amazon prime, 3day shipping) if available on the page.",
    # )

    # original_price: str = Field(
    #     ..., description="Include the currency inside the response."
    # )
    price: str = Field(..., description="Include the currency inside the response.")
    # available_colors: list[str] = Field(
    #     ...,
    #     description="Please list the colors that are available for this product if applicable.",
    # )
    available_sizes: list[str] = Field(
        [],
        description="Get all the available sizes as a list of strings. I only want the sizes that are currently available, often times unavailable sizes are greyed out or similar. It's important that you only get the currently available sizes that aren't hidden.",
    )
    # unavailable_sizes: list[str] = Field(
    #     [],
    #     description="Get all the unavailable sizes as a list of strings. I only want the sizes that are currently unavailable, often times unavailable sizes are greyed out or similar.",
    # )


class EcommerceResponse(BaseModel):
    variants: List[ProductData]


async def extract_data(
    url: str,
    page_html: str,
    screenshot: str,
    propery_name: str,
    propery_schema: Any,
):
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    llm_config = LLMConfig(openai_api_key=openai_api_key)

    db_prompt = f"Please extract the data with the following json schema: {propery_schema}. Create a script that can get this value."
    page_info = PageInformation(
        url=url,
        raw_html=page_html,
        interactable_element_info={},
        screenshot_base64=screenshot,
    )

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

If the value is very long you can truncate it. 

Output the json, starting with `reasoning`, and nothing else. Here is a screenshot of the website:""",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{screenshot}"},
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

    async def create_script(prompt: str):
        scrape_dto = ScrapePageDTO(
            page_information=page_info,
            llm_config=llm_config,
            prompt=prompt,
            db_prompt=db_prompt,
            expected_return_data=None,
            return_data_json_schema=propery_schema,
        )
        res = await scrape_page(scrape_dto)
        return res

    response_message = res.choices[0].message.content
    if response_message:
        try:
            json_res = extract_json(response_message)
        except Exception as e:
            print("Error parsing: ", response_message)
            return propery_name, response_message

        print("json_res: ", json_res)

        if json_res["type"] == "DATA_VISIBLE":
            prompt = f"Please extract the data from with this json schema: {propery_schema}. {json_res['reasoning']} So, the expected output from extraction script should be: \n\n{json_res['expected_value']}\n\nCreate a script that can get this value. Don't hardcode the expected outcome into the script, just make sure that the outcome matches it. (Doesn't need to be exactly the same, but similar.)"
            print("prompt: ", prompt)
            res = await create_script(prompt)
            return propery_name, res.json_data
        elif json_res["type"] == "SCRAPING_REQUIRED":
            res = await create_script(db_prompt)
            return propery_name, res.json_data
        elif json_res["type"] == "NOT_AVAILABLE":
            prompt = f"We are trying to extract the data that follows this JSON schema: {propery_schema}. This data doesn't seem to be available on the page however, so please code a short script that returns a value that matches the schema but returns a value like -1 or 'Not available'."
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
    page: DendritePage, browser: DendriteRemoteBrowser, use_cache: bool = False
) -> List[PageInformation]:
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    llm_config = LLMConfig(openai_api_key=openai_api_key)

    if use_cache:
        variant_buttons = await page.get_interactions_selector(
            json_res["interaction_prompt"]
        )

    page_info = await page.get_page_information()
    entire_prompt = f"""Hi, we are trying to extract product data from a webpage. Can you help me see if there are any variant of this product displayed on the page? Often times these are color variants, but it could be theme too or something else.

Please look at the page and output one of the following:

- Output {{"reasoning": "...", "type": "VARIANTS_AVAILABLE", "interaction_prompt": "..."}} if there are some kind of variant of the same product you are looking at now. 'interaction_prompt' is a prompt that will be sent to an AI agent that has the task of fetching the relevant variant selection elements. 
- Output {{"reasoning": "...", "type": "NOT_AVAILABLE"}} if there are no variants, or only one variant.

Output the json with tripple backticks like in this example:

```json
{{"reasoning": "Underneath the price three product color variants are visible. They are buttons in a row with small product previews. The current color is 'snow white', the two other colors are 'fire red', 'ocean blue'.", "type": "VARIANTS_AVAILABLE", "interaction_prompt": "Please find the buttons responsible for selecting the different product variants. They are buttons in a row with small product preview images with the colors 'snow white', 'fire red', 'ocean blue'. They are underneath the text 'mega pc gamer 100€' and above the 'chose size' text."}}
```

Output the json, starting with reasoning, and nothing else. Make sure you use a lot of texts from the website to anchor the position of the relevant element. Here is a screenshot of the website:"""

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
                json_res["interaction_prompt"]
            )
            print("variant_buttons: ", variant_buttons)

            page_infos = []
            count = await variant_buttons.count()
            for index in range(count):
                try:
                    res = await variant_buttons.nth(index).click(timeout=0)
                    active_page = await browser.get_active_page()
                    await asyncio.sleep(0.2)
                    page_info = await active_page.get_page_information()
                    page_infos.append(page_info)
                except Exception as e:
                    pass
            return page_infos
        elif json_res["type"] == "NOT_AVAILABLE":
            page_info = await page.get_page_information()
            return [page_info]

    raise Exception("Failed to parse OpenAI message.")


async def extract_product_data(url: str) -> EcommerceResponse:
    json_schema = ProductData.model_json_schema()
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    print("json_schema: ", json_schema)

    dendrite_browser = DendriteRemoteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        dendrite_api_key=os.environ.get("DENDRITE_API_KEY", ""),
    )
    print(" launch: ", url)

    await dendrite_browser.launch()
    page = await dendrite_browser.goto(url, scroll_through_entire_page=False)

    variant_pages = await get_all_product_variants(page, dendrite_browser)
    print("Found this many variants: ", len(variant_pages))
    # info = await page.get_page_information()
    # variant_pages = [info]

    page_data_results = []
    for page_info in variant_pages:
        tasks = []
        for propery_name, propery_schema in json_schema["properties"].items():
            tasks.append(
                extract_data(
                    page_info.url,
                    page_info.raw_html,
                    page_info.screenshot_base64,
                    propery_name,
                    propery_schema,
                )
            )

        results = await asyncio.gather(*tasks)
        response_data = {}
        for res in results:
            response_data[res[0]] = res[1]

        print("response_data: ", response_data)
        page_data_results.append(response_data)

    print("page_data_results: ", page_data_results)

    return EcommerceResponse(variants=page_data_results)


asyncio.run(
    extract_product_data(
        "https://www.amazon.com/Portable-Mechanical-Keyboard-MageGee-Backlit/dp/B098LG3N6R/ref=sr_1_2?_encoding=UTF8&content-id=amzn1.sym.12129333-2117-4490-9c17-6d31baf0582a&dib=eyJ2IjoiMSJ9.xPISJOYMxoc_9dHbx858fxwpXnhNZrtv8JW5ZP3BaCjqaHIK38QAFzAsY9vAczkOx_jT47M5saeEynDwm1y20JZ85TVB8YZ7cwvsm0LDrBK1PUvuJ-xGXkNcVHVIhrQc9kBmR5169dJ6bjz3i9LTKih1i1gw9zMA5shlsZn0KaVLU1EJAlCk2vS5bmQ5Idk0jdUQzbe1NHHkPD6bd_mIL2J7EUeyr51zzG5sIHNZF8s.0rZvfrTY0gQfCCR3e3ZG37IngUeL9TvLAKFP0uxXQm8&dib_tag=se&keywords=gaming%2Bkeyboard&pd_rd_r=a3b11a83-7bdf-42ad-8ccc-850a2a9be0ae&pd_rd_w=thyAn&pd_rd_wg=QuR3V&pf_rd_p=12129333-2117-4490-9c17-6d31baf0582a&pf_rd_r=EGJ9WE3PH43XY2VRNXYS&qid=1719385097&sr=8-2&th=1"
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
