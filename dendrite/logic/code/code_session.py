import json  # Important to keep since it is used inside the scripts
import re  # Important to keep since it is used inside the scripts
import sys
import traceback
from datetime import datetime  # Important to keep since it is used inside the scripts
from typing import Any, List, Optional

from bs4 import BeautifulSoup
from jsonschema import validate
from loguru import logger

from ..dom.truncate import truncate_long_string


class InterpreterError(Exception):
    pass


def custom_exec(
    cmd,
    globals=None,
    locals=None,
):
    try:
        exec(cmd, globals, locals)
    except SyntaxError as err:
        error_class = err.__class__.__name__
        detail = err.args[0]
        line_number = err.lineno
    except Exception as err:
        error_class = err.__class__.__name__
        detail = err.args[0]
        cl, exc, tb = sys.exc_info()
        line_number = traceback.extract_tb(tb)[-1][1]
    else:
        return

    traceback_desc = traceback.format_exc()
    raise InterpreterError(
        f"{error_class} at line {line_number}. Detail: {detail}. Exception: {traceback_desc}"
    )


class CodeSession:
    def __init__(self):
        self.local_vars = {"soup": None, "html_string": "", "datetime": datetime}

    def get_local_var(self, name: str) -> Any:
        try:
            return self.local_vars[name]
        except Exception as e:
            return f"Error: Couldn't get local var with name {name}. Exception: {e}"

    def add_variable(self, name: str, value: Any):
        self.local_vars[name] = value

    def exec_code(
        self,
        code: str,
        soup: Optional[BeautifulSoup] = None,
        html_string: Optional[str] = None,
    ):
        try:
            self.local_vars["soup"] = soup
            self.local_vars["html_string"] = html_string
            self.local_vars["datetime"] = datetime

            copied_vars = self.local_vars.copy()

            try:
                exec(code, globals(), copied_vars)
            except SyntaxError as err:
                error_class = err.__class__.__name__
                detail = err.args[0]
                line_number = err.lineno
                raise InterpreterError(
                    "%s at line %d, detail: %s" % (error_class, line_number, detail)
                )
            except Exception as err:
                error_class = err.__class__.__name__
                detail = err.args[0]
                _, _, tb = sys.exc_info()
                line_number = traceback.extract_tb(tb)[-1][1]
                traceback_desc = traceback.format_exc()
                raise InterpreterError(
                    "%s at line %d, detail: %s"
                    % (error_class, line_number, traceback_desc)
                )

            created_vars = {
                k: v for k, v in copied_vars.items() if k not in self.local_vars
            }

            self.local_vars = copied_vars
            return created_vars

        except Exception as e:
            raise Exception(f"Code failed to run. Exception: {e}")

    def validate_response(self, return_data_json_schema: Any, response_data: Any):
        if return_data_json_schema != None:
            try:
                validate(
                    instance=response_data,
                    schema=return_data_json_schema,
                )
            except Exception as e:
                raise e

    def llm_readable_exec_res(
        self, variables, prompt: str, attempts: int, max_attempts: int
    ):
        response = "Code executed.\n\n"

        if len(variables) == 0:
            response += "No new variables were created."
        else:
            response += "Newly created variables:"
            for var_name, var_value in variables.items():
                show_length = 600 if var_name == "response_data" else 300

                try:
                    if var_value is None:
                        str_value = "None"
                    else:
                        str_value = str(var_value)

                except Exception as e:
                    logger.error(
                        f"Error converting to string for display: {e},\nvar_name: {var_name} | var_value{var_value}"
                    )
                    str_value = "<Error converting to string for display>"

                truncated = truncate_long_string(
                    str_value, max_len_end=show_length, max_len_start=show_length
                )
                extra_info = ""
                if isinstance(var_value, List):
                    extra_info = f"\n{var_name}'s length is {len(var_value)}."
                response += f"\n\n`{var_name}={truncated}`{extra_info}"

        response += f"\n\nDo these variables match the expected values? Remember, this is what the user asked for:\n\n{prompt}\n\nIf not, try again and remember, if one approach fails several times you might need to reinspect the DOM and try a different approach. You have {max_attempts - attempts} attempts left to try and complete the task. If you are happy with the results, output a success message."

        return response


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
