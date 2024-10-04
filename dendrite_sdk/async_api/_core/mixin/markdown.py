from typing import Optional
from dendrite_sdk.async_api._core.mixin.extract import ExtractionMixin
from dendrite_sdk.async_api._core.protocol.page_protocol import DendritePageProtocol

from markdownify import markdownify as md


class MarkdownMixin(ExtractionMixin, DendritePageProtocol):
    async def markdown(self, prompt: Optional[str] = None):
        page = await self._get_page()
        page_information = await page.get_page_information()
        if prompt:
            extract_prompt = f"Extract and return the html for this requested section of the website:\n\n{prompt}"
            res = await self.extract(extract_prompt, str)
            return md(res, heading_style="ATX")
        else:
            return md(page_information.raw_html)
