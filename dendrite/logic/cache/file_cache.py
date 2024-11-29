import json
import threading
from hashlib import md5
from pathlib import Path
from typing import Dict, Generic, Type, TypeVar, Union

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class FileCache(Generic[T]):
    def __init__(self, model_class: Type[T], filepath: Union[str, Path] = "./cache.json"):
        self.filepath = Path(filepath)
        self.model_class = model_class
        self.lock = threading.RLock()
        self.cache: Dict[str, T] = {}

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

                # Convert each entry back to the model class
                self.cache = {
                    k: self.model_class.model_validate_json(json.dumps(v))
                    for k, v in raw_dict.items()
                }
            except (json.JSONDecodeError, FileNotFoundError):
                self.cache = {}

    def _save_cache(self, cache_dict: Dict[str, T]) -> None:
        """Save cache to file"""
        with self.lock:
            # Convert models to dict before saving
            serializable_dict = {
                k: json.loads(v.model_dump_json()) for k, v in cache_dict.items()
            }
            self.filepath.write_text(json.dumps(serializable_dict, indent=2))

    def get(self, key: Union[str,Dict[str,str]]) -> Union[T, None]:
        hashed_key = self.hash(key)
        return self.cache.get(hashed_key)

    def set(self, key: Union[str, Dict[str, str]], value: T) -> None:
        hashed_key = self.hash(key)
        with self.lock:
            self.cache[hashed_key] = value
            self._save_cache(self.cache)

    def delete(self, key: str) -> None:
        hashed_key = self.hash(key)
        with self.lock:
            if hashed_key in self.cache:
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
