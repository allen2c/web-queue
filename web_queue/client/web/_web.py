import asyncio
import logging
import secrets
import typing

import bs4
import fastapi
import httpx
import yarl
from playwright._impl._api_structures import ViewportSize
from playwright.async_api import async_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from str_or_none import str_or_none

from web_queue.client import WebQueueClient
from web_queue.utils.compression import compress, decompress
from web_queue.utils.human_delay import human_delay
from web_queue.utils.page_with_init_script import page_with_init_script
from web_queue.utils.simulate_mouse_circling import simulate_mouse_circling
from web_queue.utils.simulate_scrolling import simulate_scrolling

logger = logging.getLogger(__name__)


class Web:
    USER_AGENTS: typing.ClassVar[typing.Tuple[typing.Text, ...]] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # noqa: E501
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # noqa: E501
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # noqa: E501
    )
    VIEWPORT_SIZES: typing.ClassVar[typing.Tuple[typing.Tuple[int, int], ...]] = (
        (1920, 1080),
        (1366, 768),
        (1440, 900),
    )

    def __init__(self, client: WebQueueClient):
        self.client = client

    async def fetch(
        self,
        url: typing.Text | yarl.URL | httpx.URL,
        *,
        human_delay_base_delay: float = 1.2,
        dynamic_content_loading_delay: float = 2.0,
    ) -> bs4.BeautifulSoup:
        _url = str_or_none(str(url))
        if not _url:
            raise fastapi.exceptions.HTTPException(status_code=400, detail="Empty URL")

        html_content: typing.Text | None = None

        maybe_html_content = self.client.settings.web_cache.get(_url)
        if maybe_html_content:
            logger.debug(f"Hit web cache for {_url}")
            html_content = await asyncio.to_thread(
                decompress, maybe_html_content, format="zstd"
            )
            return bs4.BeautifulSoup(html_content, "html.parser")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                ],
            )

            # Create context
            _viewport_size = secrets.choice(self.VIEWPORT_SIZES)
            _viewport = ViewportSize(width=_viewport_size[0], height=_viewport_size[1])
            context = await browser.new_context(
                user_agent=secrets.choice(self.USER_AGENTS),
                viewport=_viewport,
                locale="en-US",
                timezone_id="Asia/Tokyo",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",  # noqa: E501
                },
            )

            # Create new page
            page = await context.new_page()

            # Inject script to hide automation features
            page = await page_with_init_script(page)

            try:
                # Navigate to URL
                try:
                    await page.goto(
                        _url, wait_until="domcontentloaded", timeout=4000  # 4 seconds
                    )  # Wait for network idle
                except PlaywrightTimeoutError:
                    logger.info(f"Timeout for goto '{_url}', continuing...")
                await human_delay(human_delay_base_delay)  # Initial delay

                # Wait for full page load (additional checks)
                await page.wait_for_load_state("domcontentloaded")
                await human_delay(human_delay_base_delay)

                # Simulate smooth mouse circling three times
                for _ in range(3):
                    await simulate_mouse_circling(page, _viewport)
                    await human_delay(human_delay_base_delay)

                # Simulate scrolling three times
                for _ in range(3):
                    await simulate_scrolling(page)
                    await human_delay(human_delay_base_delay)

                # Extra delay for dynamic content loading
                await human_delay(dynamic_content_loading_delay)

                # Get full HTML content
                html_content = await page.content()
                html_content = str_or_none(html_content)
                html_content_size = len(html_content or " ")

                logger.info(
                    f"Fetched HTML content size: {html_content_size} for {_url}"
                )

            finally:
                await browser.close()

        if not html_content:
            raise fastapi.exceptions.HTTPException(
                status_code=500, detail="Failed to fetch content"
            )

        await asyncio.to_thread(
            self.client.settings.web_cache.set,
            _url,
            compress(html_content, format="zstd"),
        )

        return bs4.BeautifulSoup(html_content, "html.parser")
