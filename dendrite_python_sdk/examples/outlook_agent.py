import asyncio
import os
import base64

import anthropic
from anthropic.types import Message, TextBlock
from dendrite_python_sdk import DendriteBrowser
from dendrite_python_sdk.dendrite_browser.DendritePage import DendritePage


async def open_unread_emails(page: DendritePage, subject: str):
    unread_email_el = await page.get_element(subject)
    await unread_email_el.click()

    res = await page.ask("Is the 'expand conversation' button available? If it is, return true since we want to click it. If 'collapse conversation' is available, return false", bool)

    if res.return_data == True:
        expand_conversation_button = await page.get_element("The 'expand conversation' button")
        await expand_conversation_button.click()

    messages = await page.get_elements("Every message in the conversation")
    screenshots = []
    for message_el in messages:
        image_data = await message_el.get_playwright_locator().screenshot(type="jpeg", timeout=20000)

        if image_data == None:
            return ""

        screenshots.append(base64.b64encode(image_data).decode())
    
    # Create a directory to store screenshots if it doesn't exist
    os.makedirs("test", exist_ok=True)

    # Save each screenshot to the directory with a unique name
    for i, screenshot in enumerate(screenshots):
        filename = f"test/screenshot_{i}.jpg"
        with open(filename, "wb") as file:
            file.write(base64.b64decode(screenshot))

    print(f"All screenshots have been saved to the 'test' directory.")
    

async def analyze_email_content(screenshots):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

    

    user_content = []

    for screenshot in screenshots:
        user_content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": screenshot,
                        },
                    })

    messages =[{"role": "user", "content": user_content}]
    config = {
        "system": "Look at the emails in the thread and draft a response. Your name is 'Dendrite'.",
        "messages": messages,
        "model": "claude-3-5-sonnet-20240620",
        "temperature": 0.3,
        "max_tokens": 1500,
    }

    client = anthropic.AsyncAnthropic(api_key=api_key)
    response: Message = await client.messages.create(**config)
    if isinstance(response.content[0], TextBlock):
        text = response.content[0].text
        return text

# Modify the open_unread_emails function to use the new analyze_email_content function
async def open_unread_emails(page: DendritePage, subject: str):
    unread_email_el = await page.get_element(subject)
    await unread_email_el.click()

    res = await page.ask("Is the 'expand conversation' button available? If it is, return true since we want to click it. If 'collapse conversation' is available, return false", bool)

    if res.return_data == True:
        expand_conversation_button = await page.get_element("The 'expand conversation' button")
        await expand_conversation_button.click()

    messages = await page.get_elements("Every message in the conversation")
    screenshots = []
    for message_el in messages:
        image_data = await message_el.get_playwright_locator().screenshot(type="jpeg", timeout=20000)

        if image_data == None:
            return ""

        screenshots.append(base64.b64encode(image_data).decode())
    
    # Create a directory to store screenshots if it doesn't exist
    os.makedirs("test", exist_ok=True)

    # Save each screenshot to the directory with a unique name
    for i, screenshot in enumerate(screenshots):
        filename = f"test/screenshot_{i}.jpg"
        with open(filename, "wb") as file:
            file.write(base64.b64decode(screenshot))

    print(f"All screenshots have been saved to the 'test' directory.")
    
    # Analyze the email content using Claude API
    email_summary = await analyze_email_content(screenshots)
    print(f"Email summary for subject '{subject}':")
    print(email_summary)


async def read_unread_emails():
    browser = DendriteBrowser()
    await browser.authenticate("https://outlook.live.com/mail/0/")
    page = await browser.goto("https://outlook.live.com/mail/0/")
    await page.wait_for("The emails and dashboard to be loaded")
    view_tab = await page.get_element("the 'View' tab next to home and help")
    await view_tab.click()

    filter_emails = await page.get_element(
        "The filter emails button with the filter icon"
    )
    await filter_emails.click()

    unread_emails_option = await page.get_element(
        "The Unread emails option in the filter dropdown"
    )
    await unread_emails_option.click()

    ask_res = await page.ask("Are there any unread emails? If so, output an array of strings containing like this:  'senders name – subjects' for each of the unread emails so we can open them")
    for subject in ask_res.return_data:
        print("subject: ", subject)
        await open_unread_emails(page, subject)


asyncio.run(read_unread_emails())
