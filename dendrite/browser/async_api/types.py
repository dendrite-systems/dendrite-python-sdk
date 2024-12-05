import inspect
from typing import Any, Dict, Literal, Type, TypeVar, Union

from playwright.async_api import Page
from pydantic import BaseModel

Interaction = Literal["click", "fill", "hover"]

T = TypeVar("T")
PydanticModel = TypeVar("PydanticModel", bound=BaseModel)
PrimitiveTypes = PrimitiveTypes = Union[Type[bool], Type[int], Type[float], Type[str]]
JsonSchema = Dict[str, Any]
TypeSpec = Union[PrimitiveTypes, PydanticModel, JsonSchema]

PlaywrightPage = Page
