from dendrite.models.scripts import Script

from .file_cache import FileCache

ExtractCache = FileCache(Script, "./cache/extract.json")
