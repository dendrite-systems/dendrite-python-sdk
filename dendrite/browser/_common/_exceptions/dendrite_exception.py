import base64
import os
from typing import List, Optional, Union
from uuid import uuid4

from loguru import logger

from dendrite.browser._common._exceptions._constants import INVALID_AUTH_SESSION_MSG


class BaseDendriteException(Exception):
    """
    Base exception class for Dendrite errors.

    This exception logs the error message and can optionally include a base64-encoded screenshot.

    Args:
        message (str): The error message to log.
        screenshot_base64 (Optional[str]): Base64-encoded screenshot (if any). Defaults to None.
    """

    def __init__(self, message: str, screenshot_base64: Optional[str] = None) -> None:
        self._message = message
        logger.exception(self)
        super().__init__(message)

    @property
    def message(self) -> str:
        """
        Get the error message.

        Returns:
            str: The error message.
        """
        return self._message

    def __str__(self) -> str:
        """
        Return a string representation of the exception.

        Returns:
            str: A string representation of the exception class and its message.
        """
        return f"{self.__class__.__name__}: {self.message}"


class MissingApiKeyError(BaseDendriteException):
    """
    Exception raised when the API key is missing.

    Inherits from BaseDendriteException.
    """

    def __init__(self, message: str):
        """
        Initialize the MissingApiKeyError.

        Args:
            message (str): The error message indicating the missing API key.
        """
        super().__init__(message)


class PageConditionNotMet(BaseDendriteException):
    """
    Exception raised when a required page condition is not met.

    Inherits from BaseDendriteException.
    """

    def __init__(self, message: str, screenshot_base64: Optional[str] = None):
        """
        Initialize the PageConditionNotMet error.

        Args:
            message (str): The error message indicating the condition failure.
            screenshot_base64 (Optional[str]): Base64-encoded screenshot showing the page at the time of failure.
        """
        super().__init__(message)


class InvalidAuthSessionError(BaseDendriteException):
    """
    Exception raised when the authentication session is invalid.

    Inherits from BaseDendriteException.
    """

    def __init__(
        self,
        domain: Union[str, List[str]],
        message: str = INVALID_AUTH_SESSION_MSG,
    ) -> None:
        """
        Initialize the InvalidAuthSessionError.

        Args:
            domain (Union[str, List[str]]): The domain(s) where the invalid session occurred.
            message (str, optional): The error message template. Defaults to INVALID_AUTH_SESSION_MSG.
        """
        self._domain = domain
        message = message.format(domain=domain)
        super().__init__(message)


class IncorrectOutcomeError(BaseDendriteException):
    """
    Exception raised when the outcome of an interaction is incorrect.

    Inherits from BaseDendriteException.
    """


class BrowserNotLaunchedError(BaseDendriteException):
    """
    Exception raised when the browser is not launched.

    Inherits from BaseDendriteException.
    """

    def __init__(
        self,
        message: str = "The browser should have been automatically launched by the AsyncDendrite object.. Please reach out to us on GitHub or Discord if you are facing this issue.",
    ) -> None:
        """
        Initialize the BrowserNotLaunchedError.

        Args:
            message (str, optional): The error message indicating the browser launch failure. Defaults to a predefined message.
        """
        super().__init__(message)


class DendriteException(BaseDendriteException):
    """
    General exception class for Dendrite errors, including optional screenshot and additional metadata.
    """

    def __init__(self, message: str, screenshot_base64: str = "") -> None:
        """
        Initialize the DendriteException.

        Args:
            message (str): The error message.
            screenshot_base64 (str, optional): Base64-encoded screenshot. Defaults to an empty string.
        """
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
        """
        Get the name of the exception.

        Returns:
            Optional[str]: The name of the exception, if available.
        """
        return self._name

    @property
    def stack(self) -> Optional[str]:
        """
        Get the stack trace of the exception.

        Returns:
            Optional[str]: The stack trace of the exception, if available.
        """
        return self._stack

    def store_exception_screenshot(self, path: str, name: str = "") -> str:
        """
        Store the base64-encoded screenshot as a file.

        Args:
            path (str): The directory path where the screenshot should be saved.
            name (str, optional): The name of the file. If not provided, a unique name will be generated. Defaults to an empty string.

        Returns:
            str: The full file path of the stored screenshot.
        """
        if not name:
            name = str(uuid4())

        # Create the full file path
        filepath = os.path.join(path, f"{name}.png")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Decode the Base64 string
        screenshot_data = base64.b64decode(self._screenshot_base64)

        # Write the decoded data to the specified file
        with open(filepath, "wb") as file:
            file.write(screenshot_data)

        return filepath
