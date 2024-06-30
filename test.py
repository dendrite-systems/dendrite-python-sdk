# import json
# from time import sleep
# from playwright.sync_api import sync_playwright


# browser = sync_playwright().start().chromium.launch(headless=False)

# browser.new_page().goto("https://mail.google.com/mail/u/1/#inbox")

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

dto = UploadSessionDTO(
    user_id="coffecup25",
    domain="gmail.com",
    session_data=cookies
)

request_handler.config["dendrite_api_key"] = os.environ.get("DENDRITE_API_KEY", "")

async def async_test():
    await request_handler.upload_session_data(dto)

asyncio.run(async_test())