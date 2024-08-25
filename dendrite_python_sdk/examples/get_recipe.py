import asyncio
import time
from dendrite_python_sdk.dendrite_browser.DendriteBrowser import DendriteBrowser
from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam


def ai_request(prompt: str):
    openai = OpenAI()
    messages = [ChatCompletionUserMessageParam(role="user", content=prompt)]
    oai_res = openai.chat.completions.create(messages=messages, model="gpt-4o-mini")
    if oai_res.choices[0].message.content:
        return oai_res.choices[0].message.content
    raise Exception("Failed to get successful response from Open AI.")


async def find_recipe(recipe: str, preferences: str):
    start_time = time.time()
    dendrite = DendriteBrowser()
    page = await dendrite.goto("https://www.ica.se/recept/")

    close_cookies_button = await page.get_element(
        "The reject cookies button", use_cache=False
    )
    if close_cookies_button:
        print("close_cookies_button: ", close_cookies_button.locator)
        await close_cookies_button.click()

    search_bar = await page.get_element(
        "The search bar for searching recipes with placeholder sök ingrediens etc",
        use_cache=False,
    )
    await search_bar.fill(recipe)
    await page.keyboard.press("Enter")

    await page.wait_for("Wait for the recipies to be loaded")
    await page.scroll_to_bottom()
    recipes_res = await page.extract(
        "Get all the recipes on the page and return and array of dicts like this {{name: str, time_to_make: str, url_to_recipe: str}}"
    )

    print("recipes_res.return_data: ", recipes_res.return_data)

    find_recipe_prompt = f"""Here are some recipes:
    
    {recipes_res.return_data}
    
    Please output the url of the recipe that best suits these food preferences: {preferences}. 
    
    Important: You output should consist of only one valid URL, nothing else, pick the one that best suits my preferences."""

    url = ai_request(find_recipe_prompt)
    page = await dendrite.goto(url)
    res = await page.ask(
        "Please output a nice, readable string containing the page's recipe that contains a header for ingredients and one for the steps in English.",
        str,
    )
    print(f"Find recipe took: {time.time() - start_time }. Here is the recipe: {res}")
    return res.return_data


res = asyncio.run(
    find_recipe(
        "tacos", "I am vegetarian and I want to cook something in less than 30 mins"
    )
)

print("res: ", res)
