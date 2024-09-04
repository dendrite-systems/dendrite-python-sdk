import asyncio
from contextvars import ContextVar
import functools
import json
import time
from typing import Any, Dict, List, Literal, Optional, TypeVar, Union
from uuid import uuid4
from loguru import logger as loguru_logger
from pydantic import BaseModel, Field

from dendrite_sdk._exceptions.dendrite_exception import DendriteException

class DendriteLoggerEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    message: str
    timestamp: float = Field(default_factory=time.time)
    image_base64: Optional[str] = None
    metadata: Dict[str, Any] = {}

    def __repr__(self):
        # Get the class name dynamically
        class_name = type(self).__name__
        # Truncate image_base64 to 64 characters if present
        truncated_image_base64 = (
            self.image_base64[:64] + "..." if self.image_base64 and len(self.image_base64) > 64 else self.image_base64
        )
        return (
            f"{class_name}(id={self.id}, type={self.type}, message={self.message}, "
            f"timestamp={self.timestamp}, image_base64={truncated_image_base64}, metadata={self.metadata})"
        )

    def __str__(self):
        return self.__repr__()

class DendriteInteractionEvent(DendriteLoggerEvent):
    type: Literal["interaction"] = "interaction"

    def __init__(self, action: str, element: str, message: Optional[str] = None, image_base64: Optional[str] = None, **data):
        super().__init__(
            type="interaction",
            message=message or f"Performing action '{action}' on element '{element}'",
            metadata={"action": action, "element": element},
            image_base64=image_base64,
            **data
        )

class DendriteExceptionEvent(DendriteLoggerEvent):
    type: Literal["exception"] = "exception"

    def __init__(self, exception: Union[DendriteException, Exception], image_base64: Optional[str] = None, **data):
        if isinstance(exception, DendriteException):
            image_base64 = exception._screenshot_base64
        super().__init__(
            type="exception",
            message=str(exception),
            metadata={"exception_type": type(exception).__name__},
            image_base64=image_base64,
            **data
        )

class DendriteQueryEvent(DendriteLoggerEvent):
    type: Literal["query"] = "query"
    query: str

class DendriteQueryResponseEvent(DendriteLoggerEvent):
    type: Literal["query_response"] = "query_response"
    query_id: str

EventType = TypeVar("EventType", bound=DendriteLoggerEvent)

class DendriteLoggerContext(BaseModel):
    name: str
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    elapsed_time: Optional[float] = None
    events: List[DendriteLoggerEvent] = []

    def end(self):
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time

    def add_event(self, event: DendriteLoggerEvent):
        self.events.append(event)

    def to_dict(self):
        return {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "elapsed_time": self.elapsed_time,
            "events": [event.dict() for event in self.events]
        }

class DendriteLogger:
    def __init__(self, output_path: str):
        self._output_path: str = output_path
        self._context_stack: List[DendriteLoggerContext] = []
        self._finalized_contexts: List[DendriteLoggerContext] = []

    def add_event(self, event: DendriteLoggerEvent):
        if self._context_stack:
            self._context_stack[-1].add_event(event)

    def error(self, exception: Union[DendriteException, Exception]):
        event = DendriteExceptionEvent(exception)
        self.add_event(event)

    def segment_start(self, name: str):
        context = DendriteLoggerContext(name=name)
        self._context_stack.append(context)

    def segment_end(self):
        if self._context_stack:
            context = self._context_stack.pop()
            context.end()
            self._finalized_contexts.append(context)
            loguru_logger.debug(f"Finalized Contexts: {self._finalized_contexts}")

    def to_json(self):
        loguru_logger.debug("Finalizing dendrite logger")
        data = [context.to_dict() for context in self._finalized_contexts]
        with open(self._output_path, "w") as f:
            json.dump(data, f, indent=2)
        loguru_logger.debug(f"JSON log file created: {self._output_path}")

def log_segment(name: str):
    def logging_segment(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            _logger = DENDRITE_LOGGER_CONTEXTVAR.get()
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
                _logger.segment_end()

                if result is not None:
                    return result
            
        return wrapper
    return logging_segment

DENDRITE_LOGGER_CONTEXTVAR: ContextVar[Union[DendriteLogger, None]] = ContextVar("dendrite_logger", default=None)
