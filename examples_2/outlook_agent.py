import asyncio
import os
from typing import Tuple

import anthropic
from anthropic.types import Message, ToolUseBlock
from dendrite_python_sdk import DendriteBrowser
from dendrite_python_sdk import DendritePage


def fake_knowledge_rag():
    return "Dendrite Toothpaste costs 440$. Dendrite does not have a physical store, it only sells online. Dendrite is a toothpaste does not do refunds. Dendrite toothpaste can explode if left in the sun for too long."


async def answer_email(screenshots) -> Tuple[bool, str]:
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
            }
        )

    messages = [{"role": "user", "content": user_content}]
    knowledge = fake_knowledge_rag()
    client = anthropic.AsyncAnthropic(api_key=api_key)
    response: Message = await client.messages.create(
        system=f"Look at the emails in the thread and draft a response if suitable. If you cannot answer because you don't know the answer, don't write a draft. If the email is unclear, ask for clarification. Your name is 'Dendrite' and you work for Dendrite Toothpaste Supreme. Only answer the customers direct question. Here is some knowledge: {knowledge}",
        messages=messages,  # type: ignore
        model="claude-3-5-sonnet-20240620",
        temperature=0.3,
        max_tokens=1500,
        tools=[
            {
                "name": "create_draft",
                "description": "If you want to respond to the email, use this tool.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "draft": {
                            "type": "string",
                        }
                    },
                },
            }
        ],
    )
    for content in response.content:
        if isinstance(content, ToolUseBlock):
            if content.name == "create_draft":
                text = content.input["draft"]  # type: ignore
                return True, text

    return False, response.content[0].text  # type: ignore


async def open_unread_emails(page: DendritePage, subject: str):
    unread_email_el = await page.get_element(subject)
    await unread_email_el.click()

    view_tab = await page.get_element("the 'View' tab next to home and help")
    await view_tab.click()

    res = await page.ask(
        "Is the 'expand conversation' button available? If it is, return true since we want to click it. If 'collapse conversation' is available, return false",
        bool,
    )

    if res.return_data == True:
        expand_conversation_button = await page.get_element(
            "The 'expand conversation' button"
        )
        await expand_conversation_button.click()

    messages = await page.get_elements(
        "Every message in the conversation, make sure the selector works for threads with several messages"
    )
    screenshots = []
    for message_el in messages:
        base_64_screenshot = await message_el.screenshot()
        if base_64_screenshot is not None:
            screenshots.append(base_64_screenshot)

    # Analyze the email content using Claude API
    should_answer, message = await answer_email(screenshots)
    print(should_answer, message)

    if should_answer:
        home_button = await page.get_element("the 'home' tab next to view and help")
        await home_button.click()

        reply_all_button = await page.get_element(
            "the 'reply all' button next to read/unread"
        )
        await reply_all_button.click()

        replay_email_input = await page.get_element(
            "get the input box to send my draft reply in the email thread"
        )
        await replay_email_input.fill(message)

        send_button = await page.get_element("the send button to send the draft reply")
        await send_button.click()


async def read_unread_emails():
    # All relevant API keys are automatically loaded from .env
    browser = DendriteBrowser()
    await browser.authenticate("https://outlook.live.com/mail/0/")
    page = await browser.goto("https://outlook.live.com/mail/0/")
    await page.wait_for("The emails and dashboard to be loaded")

    filter_emails = await page.get_element(
        "The filter emails button with the filter icon"
    )
    await filter_emails.click()

    unread_emails_option = await page.get_element(
        "The Unread emails option in the filter dropdown"
    )
    await unread_emails_option.click()

    await page.wait_for(
        "The emails should either be fully loaded or there should be a clear indication that there are no emails"
    )
    ask_res = await page.ask(
        "Are there any unread emails? If so, output an array of strings containing like this: 'senders name – subjects' for each of the unread emails so we can open them"
    )
    for subject in ask_res.return_data:
        await open_unread_emails(page, subject)


asyncio.run(read_unread_emails())
