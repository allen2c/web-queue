import asyncio
import logging
import secrets
import time
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
        headless: bool = True,
        goto_timeout: int = 4000,  # 4 seconds
        circling_times: int = 3,
        scrolling_times: int = 3,
        human_delay_base_delay: float = 1.2,
        dynamic_content_loading_delay: float = 2.0,
    ) -> bs4.BeautifulSoup:
        _url = str_or_none(str(url))
        if not _url:
            raise fastapi.exceptions.HTTPException(status_code=400, detail="Empty URL")

        html_content: typing.Text | None = None
        h_delay = human_delay_base_delay
        d_delay = dynamic_content_loading_delay

        logger.info(f"Browser is fetching {_url}")
        maybe_html_content = self.client.settings.web_cache.get(_url)
        if maybe_html_content:
            logger.debug(f"Hit web cache for {_url}")
            html_content = await asyncio.to_thread(
                decompress, maybe_html_content, format="zstd"
            )
            return bs4.BeautifulSoup(html_content, "html.parser")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=headless,
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
                permissions=["geolocation"],
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",  # noqa: E501
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Charset": "utf-8",
                },
            )

            # Create new page
            page = await context.new_page()

            # Inject script to hide automation features
            page = await page_with_init_script(page)

            try:
                # Navigate to URL
                logger.debug(f"Navigating (timeout: {goto_timeout}ms) to {_url}")
                try:
                    await page.goto(
                        _url, wait_until="domcontentloaded", timeout=goto_timeout
                    )  # Wait for network idle
                except PlaywrightTimeoutError:
                    logger.info(f"Timeout for goto '{_url}', continuing...")
                await human_delay(h_delay)  # Initial delay

                # Wait for full page load (additional checks)
                logger.debug(f"Waiting {h_delay}s for full page load")
                await page.wait_for_load_state("domcontentloaded")
                await human_delay(h_delay)

                # Simulate smooth mouse circling three times
                start_position = None
                for i in range(circling_times):
                    logger.debug(f"Simulating mouse circling {i+1} of {circling_times}")
                    start_position = await simulate_mouse_circling(
                        page, _viewport, start_position=start_position
                    )
                    await human_delay(h_delay)

                # Simulate scrolling three times
                for i in range(scrolling_times):
                    logger.debug(f"Simulating scrolling {i+1} of {scrolling_times}")
                    await simulate_scrolling(page, scroll_direction="down")
                    await human_delay(h_delay)

                # Extra delay for dynamic content loading
                logger.debug(f"Delaying {d_delay}s for dynamic content loading")
                await human_delay(d_delay)

                # Get full HTML content
                html_content = await page.content()
                html_content = str_or_none(html_content)
                html_content_size = len(html_content or " ")

                logger.info(
                    f"Fetched HTML content size: {html_content_size} for {_url}"
                )

                # Screenshot and PDF
                snapshot_filename = f"{int(time.time()*1E3)}_{secrets.token_hex(2)}"
                screenshot_path = self.client.settings.web_screenshot_path.joinpath(
                    f"{snapshot_filename}.png"
                )
                screenshot_path.write_bytes(await page.screenshot())
                logger.info(f"Screenshot saved to {screenshot_path}")
                pdf_path = self.client.settings.web_pdf_path.joinpath(
                    f"{snapshot_filename}.pdf"
                )
                await page.pdf(path=pdf_path, print_background=True)
                logger.info(f"PDF saved to {pdf_path}")

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
