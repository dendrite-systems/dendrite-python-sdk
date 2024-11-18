from pathlib import Path
import json
import threading
from typing import Generic, TypeVar, Union, Type, Dict
from pydantic import BaseModel
from hashlib import md5

T = TypeVar('T', bound=BaseModel)

class FileCache(Generic[T]):
    def __init__(self, model_class: Type[T], filepath: str = './cache.json'):
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
                k: json.loads(v.model_dump_json())
                for k, v in cache_dict.items()
            }
            self.filepath.write_text(json.dumps(serializable_dict, indent=2))

    def get(self, key: str) -> Union[T, None]:
        hashed_key = self.hash(key)
        return self.cache.get(hashed_key)

    def set(self, key: str, value: T) -> None:
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

    def hash(self, key: str) -> str:
        return md5(key.encode()).hexdigest()
