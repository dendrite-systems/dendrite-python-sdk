from datetime import datetime
from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse

from loguru import logger

from dendrite.logic.cache.file_cache import FileCache
from dendrite.logic.code.code_session import execute
from dendrite.logic.config import Config
from dendrite.models.dto.cached_extract_dto import CachedExtractDTO
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


async def get_working_cached_script(
    prompt: str, raw_html: str, url: str, return_data_json_schema: Any, config: Config
) -> Optional[Tuple[Script, Any]]:

    if len(url) == 0:
        raise Exception("Domain must be specified")

    scripts = get_scripts(prompt, url, config.extract_cache)
    if scripts is None or len(scripts) == 0:
        return None
    logger.debug(
        f"Found {len(scripts)} scripts in cache | Prompt: {prompt} in domain: {url}"
    )

    for script in scripts:
        try:
            res = execute(script.script, raw_html, return_data_json_schema)
            return script, res
        except Exception as e:
            logger.debug(
                f"Script failed with error: {str(e)} | Prompt: {prompt} in domain: {url}"
            )
            continue

    raise Exception(
        f"No working script found in cache even though {len(scripts)} scripts were available | Prompt: '{prompt}' in domain: '{url}'"
    )
