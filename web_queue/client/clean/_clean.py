import typing

import bs4

from web_queue.client import WebQueueClient
from web_queue.utils.html_cleaner import HTMLCleaner


class Clean:
    def __init__(self, client: WebQueueClient):
        self.client = client

    def as_main_content(self, html: bs4.BeautifulSoup | str) -> bs4.BeautifulSoup:
        html = (
            bs4.BeautifulSoup(html, "html.parser")
            if isinstance(html, typing.Text)
            else html
        )

        cleaned_html = HTMLCleaner.clean_as_main_content_html_str(html)
        return bs4.BeautifulSoup(cleaned_html, "html.parser")
