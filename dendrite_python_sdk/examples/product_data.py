import os
import asyncio
from typing import Any, List
from pydantic import BaseModel, Field

from dendrite_python_sdk import DendriteRemoteBrowser
from dotenv import load_dotenv, find_dotenv

from dendrite_python_sdk.models.PageInformation import PageInformation
from dendrite_python_sdk.ai_util.generate_text import async_openai_request
from dendrite_python_sdk.ai_util.response_extract import extract_json
from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage
from dendrite_python_sdk.models.LLMConfig import LLMConfig

load_dotenv(find_dotenv())


class EcommerceRequest(BaseModel):
    url: str


# This may include things like price, tax, shipping cost, shipping options (e.g. Amazon prime, 3day shipping), product variants (size with options S, M, L or color with options blue, red, white), etc.


class EcommerceResponse(BaseModel):
    product_name: str
    product_description: str = Field(
        ...,
        description="Get any text that describes the product. Often time this is under 'about product' or similar. Normally at least a paragraph long.",
    )
    product_image_urls: list[str] = Field(
        ...,
        description="Make sure you get the images you get the large display images and not any smaller ones.",
    )
    shipping_details: str = Field(
        ...,
        description="Please list all information regarding shipping cost, shipping options (e.g. Amazon prime, 3day shipping) if available on the page.",
    )

    original_price: str = Field(
        ..., description="Include the currency inside the response."
    )
    price: str = Field(..., description="Include the currency inside the response.")
    available_colors: list[str] = Field(
        ...,
        description="Please list the colors that are available for this product if applicable.",
    )
    available_sizes: list[str] = Field(
        [],
        description="Get all the available sizes as a list of strings. I only want the sizes that are currently available, often times unavailable sizes are greyed out or similar.",
    )
    unavailable_sizes: list[str] = Field(
        [],
        description="Get all the unavailable sizes as a list of strings. I only want the sizes that are currently unavailable, often times unavailable sizes are greyed out or similar.",
    )


async def extract_data(
    url: str,
    page_html: str,
    screenshot: str,
    propery_name: str,
    propery_schema: Any,
):
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    llm_config = LLMConfig(openai_api_key=openai_api_key)

    dendrite_browser = DendriteRemoteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", "")
    )

    page = await dendrite_browser.goto(
        "https://browser-tests-alpha.vercel.app/api/download-test",
        scroll_through_entire_page=False,
    )

    # Fetch the correct size images
    # Click on the variants

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

- Output {{"reason": "...", "type": "BAD_SCREENSHOT"}} if the screenshot didn't render correctly.
- Output {{"reason": "...", "type": "NOT_AVAILABLE"}} if the information is completely missing from the webpage.
- Output {{"reason": "...", "type": "INTERACTION_REQUIRED"}} if you need to click or interact with the website to reveal the relevant information.
- Output {{"reason": "...", "type": "SCRAPING_REQUIRED"}} if you need to create a script to scrape the required information from the HTML. This is relevant for extracting e.g image URLs.
- Output {{"reason": "...", "type": "DATA_VISIBLE", "data": "..."}} if you can see the required data clearly on the page. 'data' should match the expected output value.

Output the json with tripple backticks like in this example:

```json
{{"reason": "The price is clearly visible on the page and equals 100 USD. It can be found right under the title and slug of the product.", "type": "DATA_AVAILABLE", "data": 100}}
```

Output the json, starting with reason, and nothing else. Here is a screenshot of the website:""",
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
        res = await scrape_data_action(scrape_dto)
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
            prompt = f"Please extract the data from with this json schema: {propery_schema}. By looking at the page I can see this value:\n\n{json_res['data']}\n\nCreate a script that can get this value. It doesn't have to be exactly the same, but close enough."
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


async def get_all_product_variants(
    page: DendritePage, browser: DendriteRemoteBrowser
) -> List[PageInformation]:
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    llm_config = LLMConfig(openai_api_key=openai_api_key)

    print("Before")
    page_info = await page.get_page_information()
    entire_prompt = f"""Hi, we are trying to extract product data from a webpage. Can you help me see if there are any variant of this product displayed on the page? Often times these are color variants, but it could be theme too or something else.

Please look at the page and output one of the following:

- Output {{"reason": "...", "type": "VARIANTS_AVAILABLE", "interaction_prompt": "..."}} if there are some kind of variant of the same product you are looking at now. 'interaction_prompt' is a prompt that will be sent to an AI agent that has the task of fetching the relevant variant selection elements. 
- Output {{"reason": "...", "type": "NOT_AVAILABLE"}} if there are no variants, or only one variant.

Output the json with tripple backticks like in this example:

```json
{{"reason": "Underneath the price three product color variants are visible. They are buttons in a row with small product previews. The current color is 'snow white', the two other colors are 'fire red', 'ocean blue'.", "type": "VARIANTS_AVAILABLE", "interaction_prompt": "Please find the buttons responsible for selecting the different product variants. They are buttons in a row with small product preview images with the colors 'snow white', 'fire red', 'ocean blue'."}}
```

Output the json, starting with reason, and nothing else. Here is a screenshot of the website:"""

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
    print("entire_prompt: ", entire_prompt)

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
            raise Exception("Error parsing: {e}: ", response_message)

        print("json_res: ", json_res)

        if json_res["type"] == "VARIANTS_AVAILABLE":
            variant_buttons = await page.get_interactable_elements(
                json_res["interaction_prompt"]
            )
            print("variant_buttons: ", variant_buttons)

            page_infos = []
            for button in variant_buttons:
                res = await button.click("That a new variant page shows up")
                active_page = await browser.get_active_page()
                page_infos.append(active_page.get_page_information())
            return page_infos

    raise Exception("Failed to parse OpenAI message.")


async def extract_product_data(url: str):
    json_schema = EcommerceResponse.model_json_schema()
    print("json_schema: ", json_schema)

    dendrite_browser = DendriteRemoteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", "")
    )
    print(" launch: ", url)

    await dendrite_browser.launch()
    print("goto(url): ", url)
    page = await dendrite_browser.goto(url, scroll_through_entire_page=True)
    print("page: ", page)

    response_data = {}
    cached_all_data = True

    variant_pages = await get_all_product_variants(page, dendrite_browser)
    print("variant_pages: ", variant_pages)
    return

    for propery_name, propery_schema in json_schema["properties"].items():
        db_prompt = f"Hi, we are extracting data from '{dto.url}'. This is the json schema: {propery_schema}. Create a script that can get this value."

        page_info = PageInformation(
            url=dto.url,
            raw_html=page_html,
            interactable_element_info={},
            screenshot_base64="",
        )
        fetch_and_run_scrape_dto = ScrapePageDTO(
            page_information=page_info,
            llm_config=llm_config,
            prompt=db_prompt,
            db_prompt=db_prompt,
            expected_return_data=None,
            return_data_json_schema=propery_schema,
        )
        res = run_script_if_cached(fetch_and_run_scrape_dto)
        if res:
            response_data[propery_name] = res.json_data
        else:
            cached_all_data = False

    if cached_all_data:
        return response_data

    variant_pages = await get_all_product_variants(dto.url, page_html, screenshot)
    return

    tasks = []
    for propery_name, propery_schema in json_schema["properties"].items():
        if propery_name not in response_data:
            tasks.append(
                extract_data(dto, page_html, screenshot, propery_name, propery_schema)
            )

    results = await asyncio.gather(*tasks)

    for res in results:
        response_data[res[0]] = res[1]

    print(response_data)
    # cost = agentops.end_session("Success")
    # print("Cost: ", cost)
    return response_data


asyncio.run(
    extract_product_data(
        "https://www.nike.com/se/en/t/pegasus-41-blueprint-older-road-running-shoes-pz105x/FN5041-100"
    )
)
