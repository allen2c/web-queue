import functools
import typing

import httpx
import yarl

if typing.TYPE_CHECKING:
    from web_queue.client.ai import AI
    from web_queue.client.clean import Clean
    from web_queue.client.config import Settings
    from web_queue.client.web import Web


class WebQueueClient:
    def __init__(self, settings: typing.Optional["Settings"] = None):
        from web_queue.client.config import Settings

        self.settings = settings or Settings()

    @functools.cached_property
    def web(self) -> "Web":
        from web_queue.client.web import Web

        return Web(self)

    @functools.cached_property
    def clean(self) -> "Clean":
        from web_queue.client.clean import Clean

        return Clean(self)

    @functools.cached_property
    def ai(self) -> "AI":
        from web_queue.client.ai import AI

        return AI(self)

    async def fetch(self, url: yarl.URL | httpx.URL | str) -> str:
        from web_queue.utils.html_to_str import htmls_to_str

        html = await self.web.fetch(url)
        html = self.clean.as_main_content(html)
        html_content_metadata = await self.ai.as_html_metadata(html)

        if not html_content_metadata:
            raise ValueError(f"Failed to retrieve content metadata for url: {url}")

        content_body_htmls = html.select(
            html_content_metadata.content_body_css_selector
        )
        if not content_body_htmls:
            raise ValueError(
                "Failed to retrieve content body by css selector "
                + f"'{html_content_metadata.content_body_css_selector}' "
                + f"for url: '{url}'"
            )

        return htmls_to_str(content_body_htmls)
