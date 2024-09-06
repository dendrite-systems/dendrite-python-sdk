import base64
import os
from typing import List, Optional, Union
from uuid import uuid4

from loguru import logger

from dendrite_sdk._exceptions._constants import INVALID_AUTH_SESSION_MSG


class BaseDendriteException(Exception):
    def __init__(self, message: str) -> None:
        self._message = message
        logger.error(self)
        super().__init__(message)

    @property
    def message(self) -> str:
        return self._message

    def __str__(self) -> str:
        return f"{self.__class__.__name__}: {self.message}"


class MissingApiKeyError(BaseDendriteException):
    pass


class NavigationError(BaseDendriteException):
    pass


class BrowserError(BaseDendriteException):
    pass


class DendriteError(BaseDendriteException):
    pass


class InvalidAuthSessionError(BaseDendriteException):
    def __init__(
        self,
        domain: Union[str, List[str]],
        message: str = INVALID_AUTH_SESSION_MSG,
    ) -> None:
        self._domain = domain
        message = message.format(domain=domain)
        super().__init__(message)


class DendriteException(Exception):
    def __init__(self, message: str, screenshot_base64: str) -> None:
        self._message = message
        self._screenshot_base64 = screenshot_base64
        self._name: Optional[str] = None
        self._stack: Optional[str] = None
        super().__init__(message)

    @property
    def message(self) -> str:
        return self._message

    @property
    def name(self) -> Optional[str]:
        return self._name

    @property
    def stack(self) -> Optional[str]:
        return self._stack

    def store_exception_screenshot(self, path: str, name: str = "") -> str:
        if not name:
            name = str(uuid4())

        # Create the full file path
        filepath = os.path.join(path, f"{name}.png")

        # print("filepath: ", filepath)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Decode the Base64 string
        screenshot_data = base64.b64decode(self._screenshot_base64)

        # Write the decoded data to the specified file
        with open(filepath, "wb") as file:
            file.write(screenshot_data)

        return filepath
