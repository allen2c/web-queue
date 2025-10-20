import functools
import typing

import httpx
import yarl

if typing.TYPE_CHECKING:
    from web_queue.client.ai import AI
    from web_queue.client.clean import Clean
    from web_queue.client.config import Settings
    from web_queue.client.web import Web
    from web_queue.types.html_content import HTMLContent


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

    async def fetch(
        self,
        url: yarl.URL | httpx.URL | str,
        *,
        headless: bool = False,
        goto_timeout: int = 4000,  # 4 seconds
        circling_times: int = 2,
        scrolling_times: int = 3,
        human_delay_base_delay: float = 1.2,
        dynamic_content_loading_delay: float = 2.0,
    ) -> "HTMLContent":
        from web_queue.types.html_content import HTMLContent
        from web_queue.utils.html_to_str import htmls_to_str

        # Fetch HTML
        html = await self.web.fetch(
            url,
            headless=headless,
            goto_timeout=goto_timeout,
            circling_times=circling_times,
            scrolling_times=scrolling_times,
            human_delay_base_delay=human_delay_base_delay,
            dynamic_content_loading_delay=dynamic_content_loading_delay,
        )

        # Clean HTML
        html = self.clean.as_main_content(html)

        # Extract content metadata
        html_metadata = await self.ai.as_html_metadata(html)

        if not html_metadata:
            raise ValueError(f"Failed to retrieve content metadata for url: {url}")

        # Extract content body
        content_body_htmls = html.select(html_metadata.content_body_css_selector)
        if not content_body_htmls:
            raise ValueError(
                "Failed to retrieve content body by css selector "
                + f"'{html_metadata.content_body_css_selector}' "
                + f"for url: '{url}'"
            )

        content_body_text = htmls_to_str(content_body_htmls)

        html_content = HTMLContent(
            title=html_metadata.title,
            author=html_metadata.author,
            chapter_id=html_metadata.chapter_id,
            chapter_number=html_metadata.chapter_number,
            content=content_body_text,
            created_date=html_metadata.created_date,
            updated_date=html_metadata.updated_date,
        )

        html_content._html = str(html)
        return html_content
