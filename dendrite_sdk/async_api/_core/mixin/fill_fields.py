import asyncio
from typing import Dict
from dendrite_sdk.async_api._core.mixin.get_element import GetElementMixin
from dendrite_sdk.async_api._core.protocol.page_protocol import DendritePageProtocol
from dendrite_sdk.async_api._exceptions.dendrite_exception import DendriteException


class FillFieldsMixin(GetElementMixin, DendritePageProtocol):

    async def fill_fields(self, fields: Dict[str, str]):
        for desc, val in fields.items():
            pass

    async def fill_one_field(
        self, description: str, value: str, use_cache: bool = True
    ):
        elem = await self.get_element(description, use_cache=use_cache)
        if elem is None:
            raise DendriteException(
                f"No element matching the description found: '{description}'"
            )
        await elem.fill(value)
