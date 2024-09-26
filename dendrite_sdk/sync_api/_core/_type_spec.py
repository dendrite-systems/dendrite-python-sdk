from abc import ABC
import inspect
from typing import Any, Dict, Literal, Type, TypeVar, Union
import playwright
import playwright.sync_api
from pydantic import BaseModel
from playwright.sync_api import Page
from dendrite_sdk.sync_api._core.models.download_interface import DownloadInterface

Interaction = Literal["click", "fill", "hover"]
T = TypeVar("T")
PydanticModel = TypeVar("PydanticModel", bound=BaseModel)
PrimitiveTypes = PrimitiveTypes = Union[Type[bool], Type[int], Type[float], Type[str]]
JsonSchema = Dict[str, Any]
TypeSpec = Union[PrimitiveTypes, PydanticModel, JsonSchema]
PlaywrightPage = Page


def to_json_schema(type_spec: TypeSpec) -> Dict[str, Any]:
    if isinstance(type_spec, dict):
        return type_spec
    if inspect.isclass(type_spec) and issubclass(type_spec, BaseModel):
        return type_spec.model_json_schema()
    if type_spec in (bool, int, float, str):
        type_map = {bool: "boolean", int: "integer", float: "number", str: "string"}
        return {"type": type_map[type_spec]}
    raise ValueError(f"Unsupported type specification: {type_spec}")


def convert_to_type_spec(type_spec: TypeSpec, return_data: Any) -> TypeSpec:
    if isinstance(type_spec, type):
        if issubclass(type_spec, BaseModel):
            return type_spec.model_validate(return_data)
        if type_spec in (str, float, bool, int):
            return type_spec(return_data)
        raise ValueError(f"Unsupported type: {type_spec}")
    if isinstance(type_spec, dict):
        return return_data
    raise ValueError(f"Unsupported type specification: {type_spec}")
