from contextvars import ContextVar
from typing import Union

from loguru import logger

from dendrite_sdk._exceptions.dendrite_exception import DendriteException
from dendrite_sdk.dendrite_logger.logger import DENDRITE_LOGGER_CONTEXTVAR, DendriteLogger, DendriteLoggerEvent




def start():

    dendrite_logger = DendriteLogger(output_path="dendrite_log.json")
    DENDRITE_LOGGER_CONTEXTVAR.set(dendrite_logger)

def add(event: DendriteLoggerEvent):
    logger = DENDRITE_LOGGER_CONTEXTVAR.get()
    if not logger:
        return
    logger.add_event(event)

def error(exception: DendriteException):
    logger = DENDRITE_LOGGER_CONTEXTVAR.get()
    if not logger:
        return
    
    logger.error(exception)

def stop():
    dendrite = DENDRITE_LOGGER_CONTEXTVAR.get()
    logger.debug(f"Finalizing logger")
    if not dendrite:
        return
    dendrite.to_json()
    DENDRITE_LOGGER_CONTEXTVAR.set(None)

# type_function_map = {}
# type_function_map[DendriteClickEvent] = 
# type_function_map[str] = handle_str
# type_function_map[list] = handle_list