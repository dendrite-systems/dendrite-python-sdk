# import json
# from time import sleep
# from playwright.sync_api import sync_playwright
# from playwright_stealth import stealth_sync


# browser = (
#     sync_playwright()
#     .start()
#     .chromium.launch(
#         headless=False, args=["--disable-blink-features=AutomationControlled"]
#     )
# )

# page = browser.new_page()
# # stealth_sync(page)

# page.goto("https://mail.google.com/mail/u/1/#inbox")

# input()

# with open("cookies.json", "w") as f:
#     f.write(json.dumps(browser.contexts[0].cookies()))


import asyncio
import json
import os
from dendrite_python_sdk.dto.UploadSessionDTO import UploadSessionDTO
import dendrite_python_sdk.request_handler as request_handler

with open("cookies.json", "r") as f:
    cookies = json.loads(f.read())

print("cookies:", cookies)

dto = UploadSessionDTO(user_id="charles", domain="gmail.com", session_data=cookies)

request_handler.config["dendrite_api_key"] = (
    "sk_cc033d231c2e7c7e5df3bca5883013a0915cd429b5ceb53f3965c7f84fd98e4d"
)


async def async_test():
    await request_handler.upload_session_data(dto)


asyncio.run(async_test())
