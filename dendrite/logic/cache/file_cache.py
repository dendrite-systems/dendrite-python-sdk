import json
import threading
from hashlib import md5
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Mapping,
    Type,
    TypeVar,
    Union,
    Optional,
    overload,
)

from pydantic import BaseModel

T = TypeVar("T", bound=Union[BaseModel, Mapping[Any, Any]])


class FileCache(Generic[T]):
    def __init__(
        self, model_class: Type[T], filepath: Union[str, Path] = "./cache.json"
    ):
        self.filepath = Path(filepath)
        self.model_class = model_class
        self.lock = threading.RLock()
        self.cache: Dict[str, List[T]] = {}

        # Create file if it doesn't exist
        if not self.filepath.exists():
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            self._save_cache({})
        else:
            self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from file into memory"""
        with self.lock:
            try:
                json_string = self.filepath.read_text()
                raw_dict = json.loads(json_string)

                # Convert each entry based on model_class type
                self.cache = {}
                for k, v_list in raw_dict.items():
                    if not isinstance(v_list, list):
                        v_list = [v_list]  # Convert old single-value format to list

                    self.cache[k] = []
                    for v in v_list:
                        if issubclass(self.model_class, BaseModel):
                            self.cache[k].append(
                                self.model_class.model_validate_json(json.dumps(v))
                            )
                        else:
                            # For any Mapping type (dict, TypedDict, etc)
                            self.cache[k].append(v)
            except (json.JSONDecodeError, FileNotFoundError):
                self.cache = {}

    def _save_cache(self, cache_dict: Dict[str, List[T]]) -> None:
        """Save cache to file"""
        with self.lock:
            # Convert entries based on their type
            serializable_dict = {}
            for k, v_list in cache_dict.items():
                serializable_dict[k] = []
                for v in v_list:
                    if isinstance(v, BaseModel):
                        serializable_dict[k].append(json.loads(v.model_dump_json()))
                    elif isinstance(v, Mapping):
                        serializable_dict[k].append(
                            dict(v)
                        )  # Convert any Mapping to dict
                    else:
                        raise ValueError(f"Unsupported type for cache value: {type(v)}")

            self.filepath.write_text(json.dumps(serializable_dict, indent=2))

    @overload
    def get(
        self, key: Union[str, Dict[str, str]], index: None = None
    ) -> Optional[List[T]]: ...

    @overload
    def get(self, key: Union[str, Dict[str, str]], index: int) -> Optional[T]: ...

    def get(
        self, key: Union[str, Dict[str, str]], index: Optional[int] = None
    ) -> Union[T, List[T], None]:
        """
        Get cached values for a key. If index is provided, returns that specific item.
        If index is None, returns the full list of items.
        Returns None if key doesn't exist or index is out of range.
        """
        hashed_key = self.hash(key)
        values = self.cache.get(hashed_key, [])

        if index is not None:
            return values[index] if 0 <= index < len(values) else None
        return values if values else None

    def set(self, key: Union[str, Dict[str, str]], values: Union[T, List[T]]) -> None:
        """
        Replace all values for a key with new value(s).
        If a single value is provided, it will be wrapped in a list.
        """
        hashed_key = self.hash(key)
        with self.lock:
            if isinstance(values, list):
                self.cache[hashed_key] = values
            else:
                self.cache[hashed_key] = [values]
            self._save_cache(self.cache)

    def append(self, key: Union[str, Dict[str, str]], value: T) -> None:
        """
        Append a single value to the list of values for a key.
        Creates a new list if the key doesn't exist.
        """
        hashed_key = self.hash(key)
        with self.lock:
            if hashed_key not in self.cache:
                self.cache[hashed_key] = []
            self.cache[hashed_key].append(value)
            self._save_cache(self.cache)

    def delete(self, key: str, index: Optional[int] = None) -> None:
        """
        Delete cached value(s). If index is provided, only that item is deleted.
        If index is None, all items for the key are deleted.
        """
        hashed_key = self.hash(key)
        with self.lock:
            if hashed_key in self.cache:
                if index is not None and 0 <= index < len(self.cache[hashed_key]):
                    del self.cache[hashed_key][index]
                    if not self.cache[hashed_key]:  # Remove key if list is empty
                        del self.cache[hashed_key]
                else:
                    del self.cache[hashed_key]
                self._save_cache(self.cache)

    def hash(self, key: Union[str, Dict]) -> str:
        """
        Create a deterministic hash from a string or dictionary.
        Handles nested structures and different value types.
        """

        def normalize_value(v):
            if isinstance(v, dict):
                return self.hash(v)
            elif isinstance(v, (list, tuple)):
                return "[" + ",".join(normalize_value(x) for x in v) + "]"
            elif v is None:
                return "null"
            elif isinstance(v, bool):
                return str(v).lower()
            else:
                return str(v).strip()

        if isinstance(key, dict):
            try:
                # Sort by normalized string keys
                sorted_pairs = [
                    f"{str(k).strip()}∴{normalize_value(v)}"  # Using a rare Unicode character as delimiter
                    for k, v in sorted(key.items(), key=lambda x: str(x[0]).strip())
                ]
                key = "❘".join(sorted_pairs)  # Using another rare Unicode character
            except Exception as e:
                raise ValueError(f"Failed to process dictionary key: {e}")

        try:
            return md5(str(key).encode("utf-8")).hexdigest()
        except Exception as e:
            raise ValueError(f"Failed to create hash: {e}")
