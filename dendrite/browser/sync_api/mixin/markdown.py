import re
from typing import Optional
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from ..mixin.extract import ExtractionMixin
from ..protocol.page_protocol import DendritePageProtocol


class MarkdownMixin(ExtractionMixin, DendritePageProtocol):

    def markdown(self, prompt: Optional[str] = None):
        page = self._get_page()
        page_information = page.get_page_information()
        if prompt:
            extract_prompt = f"Create a script that returns the HTML from one element from the DOM that best matches this requested section of the website.\n\nDescription of section: '{prompt}'\n\nWe will be converting your returned HTML to markdown, so just return ONE stringified HTML element and nothing else. It's OK if extra information is present. Example script: 'response_data = soup.find('tag', {{'attribute': 'value'}}).prettify()'"
            res = self.extract(extract_prompt)
            markdown_text = md(res)
            cleaned_markdown = re.sub("\\n{3,}", "\n\n", markdown_text)
            return cleaned_markdown
        else:
            markdown_text = md(page_information.raw_html)
            cleaned_markdown = re.sub("\\n{3,}", "\n\n", markdown_text)
            return cleaned_markdown
