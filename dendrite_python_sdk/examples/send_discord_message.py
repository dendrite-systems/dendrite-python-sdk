import os
import asyncio

from dendrite_python_sdk import DendriteBrowser
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


async def main(username: str):
    dendrite_browser = DendriteBrowser(
        openai_api_key=os.environ.get("OPENAI_API_KEY", "")
    )

    page = await dendrite_browser.goto(
        "https://discord.com/login", scroll_through_entire_page=False
    )

    # Get elements with prompts instead of using brittle selectors
    email_field = await page.get_interactable_element("The input field for email")
    password_field = await page.get_interactable_element("The input field for password")

    await email_field.fill(os.environ.get("DISCORD_USERNAME", ""))
    await password_field.fill(os.environ.get("DISCORD_PASSWORD", ""))
    await page.get_playwright_page().keyboard.press("Enter")

    # HACK: Enough time to solve recaptcha
    await asyncio.sleep(20)

    user_chat_button = await page.get_interactable_element(
        f"The chat with the user called '{username}'"
    )
    await user_chat_button.click()

    message_field = await page.get_interactable_element(
        f'The input field for inputing a message in the chat with "{username}"'
    )

    await message_field.fill(f"Hello, {username}! I am a bot. How are you doing today?")
    await page.get_playwright_page().keyboard.press("Enter")

    await asyncio.sleep(2)


asyncio.run(main("coffecup25"))
