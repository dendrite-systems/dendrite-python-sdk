from typing import Any, List, Optional, Tuple
from urllib.parse import urlparse

from loguru import logger

from dendrite.logic.cache.utils import get_script
from dendrite.logic.code.code_session import execute
from dendrite.models.scripts import Script


async def get_working_cached_script(
    prompt: str,
    raw_html: str,
    url: str,
    return_data_json_schema: Any,
) -> Optional[Tuple[Script, Any]]:

    if len(url) == 0:
        raise Exception("Domain must be specified")

    scripts: List[Script] = [get_script(prompt, url) or ...]
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

    if len(scripts) == 0:
        return None

    raise Exception(
        f"No working script found in cache even though {len(scripts)} scripts were available | Prompt: '{prompt}' in domain: '{url}'"
    )
