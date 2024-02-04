import os
from dendrite_python_sdk.DendriteAPI import DendriteAPI

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DENDRITE_API_KEY = os.environ.get("DENDRITE_API_KEY", "")


def main():
    client = DendriteAPI(api_key=DENDRITE_API_KEY)
    dto = {
        "message": "Please go to https://www.scrapethissite.com/pages/forms/ and scrape all the Team's names.",
        "store_chat":  True

    }
    res = client.complete_task(dto)

  # Description of how the results were acheived
    print(res["message"])
    # JSON containing the data from the task if there is any
    print(res["data"])

    # res = client.go_to_website(
    #     "https://medium.com", "Looking for exciting articles", False)
    # print(res["message"])

    # res = client.scroll("Finding more interesting articles", 2000)
    # print(res["message"])

    # res = client.look_at_page(
    #     "See any articles that start with the letter 'A'?")
    # print(res["message"])
