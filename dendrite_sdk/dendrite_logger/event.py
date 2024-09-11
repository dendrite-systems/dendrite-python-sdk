from contextvars import ContextVar
from typing import Any, Dict, Literal, Optional, TypedDict, Union

from loguru import logger as loguru_logger

from dendrite_sdk._exceptions.dendrite_exception import DendriteException
from dendrite_sdk.dendrite_logger.logger import (
    DENDRITE_LOGGER_CONTEXTVAR,
    DendriteLogger,
    DendriteLoggerEvent,
)


# Define the allowed log level names using Literal
LogLevel = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]


# Define a TypedDict for log levels
class LogLevelDict(TypedDict):
    TRACE: int
    DEBUG: int
    INFO: int
    SUCCESS: int
    WARNING: int
    ERROR: int
    CRITICAL: int


# Now create the log_levels dict with typing
log_levels: LogLevelDict = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "SUCCESS": 25,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


def update_current_observation(metadata: Dict[str, Any]):
    logger = DENDRITE_LOGGER_CONTEXTVAR.get()
    if not logger:
        return
    return logger._context_stack[-1].events[-1].metadata.update(metadata)


def start(name: Optional[str] = None, session_id: Optional[str] = None):
    dendrite_logger = DendriteLogger(
        output_path="dendrite_log.json", session_id=session_id
    )
    DENDRITE_LOGGER_CONTEXTVAR.set(dendrite_logger)


def add(event: DendriteLoggerEvent):
    logger = DENDRITE_LOGGER_CONTEXTVAR.get()
    if not logger:
        return
    loguru_logger.opt(depth=1).info(event.message)
    logger.add_event(event)


def log(message: str, level: LogLevel, **kwargs: Any):
    logger = DENDRITE_LOGGER_CONTEXTVAR.get()
    if not logger:
        return
    loguru_logger.opt(depth=1).log(level, message, file="dendrite_log")
    event = DendriteLoggerEvent(type="log", message=message, metadata=kwargs)
    logger.add_event(event)


def error(exception: DendriteException):
    logger = DENDRITE_LOGGER_CONTEXTVAR.get()
    if not logger:
        return

    logger.error(exception)


def stop():
    dendrite = DENDRITE_LOGGER_CONTEXTVAR.get()
    loguru_logger.debug(f"Finalizing logger")
    if not dendrite:
        return
    dendrite.to_json()
    DENDRITE_LOGGER_CONTEXTVAR.set(None)


# type_function_map = {}
# type_function_map[DendriteClickEvent] =
# type_function_map[str] = handle_str
# type_function_map[list] = handle_list
