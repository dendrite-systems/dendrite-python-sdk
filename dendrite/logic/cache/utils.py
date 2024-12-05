from datetime import datetime
from typing import List, Optional
from urllib.parse import urlparse

from dendrite.logic.cache.file_cache import FileCache
from dendrite.models.scripts import Script


def save_script(code: str, prompt: str, url: str, cache: FileCache[Script]):
    domain = urlparse(url).netloc
    script = Script(
        url=url, domain=domain, script=code, created_at=datetime.now().isoformat()
    )
    cache.append({"prompt": prompt, "domain": domain}, script)


def get_scripts(
    prompt: str, url: str, cache: FileCache[Script]
) -> Optional[List[Script]]:
    domain = urlparse(url).netloc
    return cache.get({"prompt": prompt, "domain": domain})
