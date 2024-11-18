from typing import Any

from bs4 import BeautifulSoup
from .code_session import CodeSession


def execute(script: str, raw_html: str, return_data_json_schema) -> Any:
    code_session = CodeSession()
    soup = BeautifulSoup(raw_html, "lxml")
    try:

        created_variables = code_session.exec_code(script, soup, raw_html)

        if "response_data" in created_variables:
            response_data = created_variables["response_data"]

            try:
                code_session.validate_response(return_data_json_schema, response_data)
            except Exception as e:
                raise Exception(f"Failed to validate response data. Exception: {e}")

            return response_data
        else:
            raise Exception("No return data available for this script.")
    except Exception as e:
        raise e
