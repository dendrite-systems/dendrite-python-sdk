

from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from dendrite.logic.cache import extract_cache
from dendrite.models.scripts import Script


def save_script(code: str, prompt: str, url: str):
    domain = urlparse(url).netloc
    script = Script(
        url=url, domain=domain, script=code, created_at=datetime.now().isoformat()
    )
    extract_cache.ExtractCache.set({"prompt": prompt, "domain": domain}, script)

def get_script(prompt: str, domain: str) -> Optional[Script]:
    return extract_cache.ExtractCache.get({"prompt": prompt, "domain": domain})