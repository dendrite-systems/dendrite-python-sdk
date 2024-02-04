from typing import Optional
import requests
import json


class DendriteAPI:

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://localhost:8000"  # "https://dendrite.se/api"

    def _send_request(self, endpoint, params=None, data=None, headers=None, method='GET'):
        url = f"{self.base_url}/{endpoint}"
        headers = headers or {}
        headers['Authorization'] = f'Bearer {self.api_key}'
        headers['Content-Type'] = 'application/json'

        if data is not None:
            data = json.dumps(data)

        response = requests.request(
            method, url, params=params, data=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def inspect_element(self,
                        reason: str,
                        text: Optional[str] = None,
                        dendrite_id: Optional[str] = None,
                        show_neighbors: Optional[bool] = True,
                        look_in_attributes: Optional[bool] = False):
        """
        This function allows you to look at the HTML so you can interact with it or extract its contents.
        """
        params = {
            "reason": reason,
            "text": text,
            "dendrite_id": dendrite_id,
            "show_neighbors": show_neighbors,
            "look_in_attributes": look_in_attributes
        }

        return self._send_request("inspect-element", params=params)

    def scroll(self, reason: str, amount_px: Optional[int] = 900, element_dendrite_id: Optional[str] = None):
        """
        This function provides a tool for scrolling.
        """
        params = {'reason': reason, 'amount_px': amount_px,
                  'element_dendrite_id': element_dendrite_id}
        return self._send_request('scroll', params=params)

    def list_environment_vars(self):
        """
        This function lists the names of all available environment variables.
        """
        return self._send_request('list-environment-vars')

    def go_to_website(self, url: str, reasons_for_visit: str, use_vision: Optional[bool] = None):
        """
        This function navigates to a specified website URL.
        """
        params = {
            "url": url,
            "reasons_for_visit": reasons_for_visit,
            "use_vision": use_vision
        }
        return self._send_request("go-to-website", params=params)

    def list_environment_vars(self):
        """
        This function lists all available environment variables.
        """
        return self._send_request("list-environment-vars")

    def look_at_page(self, prompt: str):
        """
        This function analyzes the current page and provides advice on what to do next.
        """
        params = {
            "prompt": prompt,
        }
        return self._send_request("look-at-page", params=params)

    def complete_task(self, complete_task_dto: dict):
        """
        This endpoint prompts our own agent to complete a webtask for you.
        """
        return self._send_request("complete-task", data=complete_task_dto, method='POST')
