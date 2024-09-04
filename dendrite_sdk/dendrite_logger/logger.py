import asyncio
from contextvars import ContextVar
import functools
import json
import time
from typing import Any, Dict, List, Literal, Optional, TypeVar, Union
from uuid import uuid4
from loguru import logger
from pydantic import BaseModel

from dendrite_sdk._exceptions.dendrite_exception import DendriteException
from .html_generator import create_html_dashboard

class DendriteLoggerEvent():

    def __init__(self, type: str, message: str, metadata: Dict[str, Any] = {}) -> None:
        self.id = str(uuid4())
        self.type = type
        self.message = message
        self.timestamp = time.time()

    def __repr__(self):
        return f"Event(id={self.id}, type={self.type}, message={self.message}, timestamp={self.timestamp})"

class DendriteInteractionEvent(DendriteLoggerEvent):
    action: str
    element: str

    def __init__(self, action: str, element: str, message: Optional[str] = None) -> None:
        self.action = action
        self.element = element
        self.timestamp = time.time()
        self.message = message or f"Performing action '{action}' on element '{element}'"
        super().__init__("interaction", self.message)

class DendriteExceptionEvent(DendriteLoggerEvent):
    def __init__(self, exception: Union[DendriteException, Exception]) -> None:
        super().__init__("exception", str(exception))

class DendriteQueryEvent(DendriteLoggerEvent):
    query: str

class DendriteQueryResponseEvent(DendriteLoggerEvent):
    query_id: str

EventType = TypeVar("EventType",bound=DendriteLoggerEvent)

class DendriteLoggerContext():
    def __init__(self, name) -> None:
        self._start_time = time.time()
        self.name = name
        self._events: List[DendriteLoggerEvent] = []
        super().__init__()

    def end(self):
        end_time = time.time()
        self.elapsed_time = end_time - self._start_time

    def add_event(self, event: DendriteLoggerEvent) -> None:
        self._events.append(event)

    def __repr__(self):
        events_repr = "\n  ".join([repr(event) for event in self._events])
        return (f"Context(name={self.name}, start_time={self._start_time}, "
                f"elapsed_time={getattr(self, 'elapsed_time', 'Not Ended')}, "
                f"events=[\n  {events_repr}\n])")

class DendriteLogger:

    def __init__(self, output_path: str) -> None:
        self._output_path: str = output_path
        self._context_stack: List[DendriteLoggerContext] = []
        self._finalized_contexts: List[DendriteLoggerContext]= []

    def add_event(self, event: DendriteLoggerEvent) -> None:
        self._context_stack[-1].add_event(event)

    def error(self, exception: Union[DendriteException,Exception]) -> None:
        event = DendriteExceptionEvent(exception)
        self._context_stack[-1].add_event(event)

    def segment_start(self, name:str) -> None:
        context = DendriteLoggerContext(name)
        self._context_stack.append(context)

    def segment_end(self) -> None:
        context=self._context_stack.pop()
        context.end()
        self._finalized_contexts.append(context)
        logger.debug(f"Finalized Contexts: {self._finalized_contexts}")

    def to_json(self):
        logger.debug("Finalizing dendrite logger")
        res = []
        for context in self._finalized_contexts:
            res.append(str(context))
        with open(self._output_path, "w") as f:
            f.write(json.dumps(res, indent=4))
        self.to_html()

    def to_html(self):
        json_file = self._output_path
        html_file = self._output_path.rsplit('.', 1)[0] + '.html'
        create_html_dashboard(json_file, html_file)
        logger.debug(f"HTML dashboard created: {html_file}")

def log_segment(name: str):
    def logging_segment(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            _logger = DENDRITE_LOGGER_CONTEXTVAR.get()
            logger.debug(f"Logger: {_logger}")
            result = None
            if not _logger:
                return await func(*args, **kwargs)
            
            _logger.segment_start(name)
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                _logger.error(e)
                raise e
            finally:
                logger.debug(f"Result: {result}")
                _logger.segment_end()

                if result is not None:
                    return result
            
        return wrapper
    return logging_segment

DENDRITE_LOGGER_CONTEXTVAR: ContextVar[Union[DendriteLogger, None]] = ContextVar("dendrite_logger", default=None)
