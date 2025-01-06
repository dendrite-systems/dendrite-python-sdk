import asyncio
import hashlib
from typing import List, Optional
from urllib.parse import urlparse

from loguru import logger

from dendrite.logic.config import Config
from dendrite.logic.extract.cache import get_scripts, get_working_cached_script
from dendrite.logic.extract.extract_agent import ExtractAgent
from dendrite.models.dto.cached_extract_dto import CachedExtractDTO
from dendrite.models.dto.extract_dto import ExtractDTO
from dendrite.models.response.extract_response import ExtractResponse
from dendrite.models.scripts import Script


async def get_cached_scripts(dto: CachedExtractDTO, config: Config) -> List[Script]:
    return get_scripts(dto.prompt, dto.url, config.extract_cache) or []


async def test_cache(
    extract_dto: ExtractDTO, config: Config
) -> Optional[ExtractResponse]:
    try:

        cached_script_res = await get_working_cached_script(
            extract_dto.combined_prompt,
            extract_dto.page_information.raw_html,
            extract_dto.page_information.url,
            extract_dto.return_data_json_schema,
            config,
        )

        if cached_script_res is None:
            return None

        script, script_exec_res = cached_script_res
        return ExtractResponse(
            status="success",
            message="Re-used a preexisting script from cache with the same specifications.",
            return_data=script_exec_res,
            created_script=script.script,
        )

    except Exception as e:
        return ExtractResponse(
            status="failed",
            message=str(e),
        )


class InMemoryLockManager:
    # Class-level dictionaries to keep track of locks and events
    locks = {}
    events = {}
    global_lock = asyncio.Lock()

    def __init__(
        self,
        extract_page_dto: ExtractDTO,
    ):
        self.key = self.generate_key(extract_page_dto)

    def generate_key(self, extract_page_dto: ExtractDTO) -> str:
        domain = urlparse(extract_page_dto.page_information.url).netloc
        key_data = f"{domain}:{extract_page_dto.combined_prompt}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def acquire_lock(self, timeout: int = 60) -> bool:
        async with InMemoryLockManager.global_lock:
            if self.key in InMemoryLockManager.locks:
                # Lock is already acquired
                return False
            else:
                # Acquire the lock
                InMemoryLockManager.locks[self.key] = True
                return True

    async def release_lock(self):
        async with InMemoryLockManager.global_lock:
            InMemoryLockManager.locks.pop(self.key, None)
            InMemoryLockManager.events.pop(self.key, None)

    async def publish(self, message: str):
        async with InMemoryLockManager.global_lock:
            event = InMemoryLockManager.events.get(self.key)
            if event:
                event.set()

    async def subscribe(self):
        async with InMemoryLockManager.global_lock:
            if self.key not in InMemoryLockManager.events:
                InMemoryLockManager.events[self.key] = asyncio.Event()
            # No need to assign to self.event; return the event instead
            return InMemoryLockManager.events[self.key]

    async def wait_for_notification(
        self, event: asyncio.Event, timeout: float = 1600.0
    ) -> bool:
        try:
            await asyncio.wait_for(event.wait(), timeout)
            return True
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout error: {e}")
            return False
        finally:
            # Clean up event
            async with InMemoryLockManager.global_lock:
                InMemoryLockManager.events.pop(self.key, None)


async def extract(extract_page_dto: ExtractDTO, config: Config) -> ExtractResponse:

    lock_manager = InMemoryLockManager(extract_page_dto)
    lock_acquired = await lock_manager.acquire_lock()

    if lock_acquired:
        return await generate_script(extract_page_dto, lock_manager, config)
    else:
        res = await wait_for_script_generation(extract_page_dto, lock_manager, config)

        if res:
            return res
        # Else create a working script since page is different
        extract_agent = ExtractAgent(extract_page_dto.page_information, config=config)
        res = await extract_agent.write_and_run_script(extract_page_dto)
        return res


async def generate_script(
    extract_page_dto: ExtractDTO, lock_manager: InMemoryLockManager, config: Config
) -> ExtractResponse:
    try:
        extract_agent = ExtractAgent(extract_page_dto.page_information, config=config)
        res = await extract_agent.write_and_run_script(extract_page_dto)
        await lock_manager.publish("done")
        return res
    except Exception as e:
        await lock_manager.publish("failed")
        raise e
    finally:
        await lock_manager.release_lock()


async def wait_for_script_generation(
    extract_page_dto: ExtractDTO, lock_manager: InMemoryLockManager, config: Config
) -> Optional[ExtractResponse]:
    event = await lock_manager.subscribe()
    logger.info("Waiting for script to be generated")
    notification_received = await lock_manager.wait_for_notification(event)

    # If script was created after waiting
    if notification_received:
        res = await test_cache(extract_page_dto, config)
        if res:
            return res
