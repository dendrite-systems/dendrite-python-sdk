import inspect
from typing import Any, Dict, TypeVar, Union
from pydantic import BaseModel


T = TypeVar("T")
PydanticModel = TypeVar("PydanticModel", bound=BaseModel)
PrimitiveType = Union[str, float, bool, int]
JsonSchema = Dict[str, Any]
TypeSpec = Union[PrimitiveType, PydanticModel, JsonSchema]


def to_json_schema(type_spec: TypeSpec) -> Dict[str, Any]:
    if isinstance(type_spec, dict):
        # Assume it's already a JSON schema
        return type_spec
    elif inspect.isclass(type_spec) and issubclass(type_spec, BaseModel):
        # Convert Pydantic model to JSON schema
        return type_spec.model_json_schema()
    elif type_spec in (bool, int, float, str):
        # Convert basic Python types to JSON schema
        type_map = {bool: "boolean", int: "integer", float: "number", str: "string"}
        return {"type": type_map[type_spec]}  # type: ignore
    else:
        raise ValueError(f"Unsupported type specification: {type_spec}")


def convert_to_type_spec(type_spec: TypeSpec, return_data: Any):
    if isinstance(type_spec, type):
        if issubclass(type_spec, BaseModel):
            return type_spec.model_validate(return_data)
        elif type_spec in (str, float, bool, int):
            return type_spec(return_data)
        else:
            raise ValueError(f"Unsupported type: {type_spec}")
    elif isinstance(type_spec, dict):
        return return_data
    else:
        raise ValueError(f"Unsupported type specification: {type_spec}")
