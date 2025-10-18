import asyncio
import datetime
import hashlib
import logging
import textwrap
import typing
import zoneinfo

import logfire
from rich.pretty import pretty_repr

from web_queue.client import WebQueueClient
from web_queue.types.html_metadata_response import HTMLMetadataResponse
from web_queue.utils.compression import compress, decompress

if typing.TYPE_CHECKING:
    import bs4

logger = logging.getLogger(__name__)


class AI:
    def __init__(self, client: WebQueueClient):
        self.client = client

    @logfire.instrument
    async def as_html_metadata(
        self, html: typing.Union["bs4.BeautifulSoup", typing.Text]
    ) -> typing.Optional[HTMLMetadataResponse]:
        """Extract content metadata and CSS selector from HTML.

        Analyzes HTML to find content body selector and extract metadata values.
        """
        openai_client = self.client.settings.openai_client
        model_name = self.client.settings.OPENAI_MODEL

        html = str(html)

        logger.info(f"AI is extracting content metadata from HTML: {html}")

        cache_key = (
            "retrieve_html_content_metadata:"
            + f"{hashlib.md5(html.encode('utf-8')).hexdigest()}"
        )

        might_cached_data: typing.Text | None = await asyncio.to_thread(
            self.client.settings.compressed_base64_cache.get, cache_key
        )
        if might_cached_data is not None:
            logger.debug(
                "Hit cache 'as_html_content_metadata':"
                + f"{pretty_repr(html, max_string=32)}"
            )
            return HTMLMetadataResponse.model_validate_json(
                decompress(might_cached_data)
            )

        # Get current time in Asia/Taipei timezone for relative date parsing
        current_time = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Taipei"))
        current_time_iso = current_time.isoformat()

        system_prompt = textwrap.dedent(
            f"""
            You are an HTML structure analysis expert. Task: From the provided HTML, extract content metadata and identify CSS selectors.

            Current time (Asia/Taipei timezone): {current_time_iso}

            Instructions:
            1. **content_body_css_selector**: Find the CSS selector for the main content body element containing ONLY the article text.
               - Look for semantic tags like <article>, <main>, or <div> with classes/IDs like 'body', 'content', 'text', 'novel-body'.
               - EXCLUDE elements containing metadata (title, author, dates, navigation, footer, ads, comments).
               - Example: 'div.article-body', 'div#novel-content', 'div.p-novel__text'.
               - Return empty string if not found.

            2. **title**: Extract the actual title text (chapter title, article title).
               - Look in <h1>, <h2>, or elements with class/id containing 'title', 'heading'.
               - Return the text content, not the CSS selector.
               - Return empty string if not found.

            3. **author**: Extract the actual author name or username.
               - Look in elements with class/id containing 'author', 'writer', 'username'.
               - Return the text content.
               - Return empty string if not found.

            4. **chapter_id**: Extract the actual chapter identifier (e.g., '12345', 'ch-001').
               - Look in data attributes, URLs, or element IDs.
               - Return empty string if not found.

            5. **chapter_number**: Extract the actual chapter number (e.g., '1', '42', 'Chapter 5').
               - Return empty string if not found.

            6. **created_date** and **updated_date**: Parse dates to ISO 8601 format with +08:00 timezone.
               - For absolute dates: Convert to 'YYYY-MM-DDTHH:MM:SS+08:00' format.
               - For relative dates ('2 days ago', '3 hours ago'): Calculate from current_time and format.
               - Return empty string if not found.

            Rules:
            - If any field is not found or unclear, return empty string "".
            - Do not guess or make up information.
            - Focus on precision and accuracy.

            Now, analyze the provided HTML and extract all available metadata.
            """  # noqa: E501
        ).strip()

        try:
            parsed_cmpl = await openai_client.chat.completions.parse(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": html},
                ],
                model=model_name,
                response_format=HTMLMetadataResponse,
            )
            response_msg = parsed_cmpl.choices[0].message
            if response_msg.refusal:
                logger.error(f"LLM refusal: {response_msg.refusal}")
                return None

            elif response_msg.parsed:
                output: HTMLMetadataResponse = response_msg.parsed
                output._html = html
                logger.info(f"LLM response: {output}")

                # Cache the response
                await asyncio.to_thread(
                    self.client.settings.compressed_base64_cache.set,
                    cache_key,
                    compress(output.model_dump_json()),
                )

                return output

            else:
                logger.error(f"LLM Error for message: {response_msg}")
                return None

        except Exception as e:
            logger.error(f"Parsing failed: {e}")
            return None
