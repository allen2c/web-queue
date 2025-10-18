import asyncio
import logging

import huey
import logfire
import logging_bullet_train as lbt
import yarl

from web_queue.client import WebQueueClient
from web_queue.config import Settings
from web_queue.types.html_content import HTMLContent

lbt.set_logger("web_queue")

logfire.configure()
logfire.instrument_openai()

logger = logging.getLogger(__name__)

logger.info("Web queue app starting...")

web_queue_settings = Settings()
__queue_url_safe = yarl.URL(
    web_queue_settings.WEB_QUEUE_URL.get_secret_value()
).with_password("***")
logger.info(f"Web queue connecting to redis: {__queue_url_safe}")

huey_app = huey.RedisHuey(
    web_queue_settings.WEB_QUEUE_NAME,
    url=web_queue_settings.WEB_QUEUE_URL.get_secret_value(),
)
wq_client = WebQueueClient()


@huey_app.task(retries=1, retry_delay=8)
def fetch_html(url: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        html_content: HTMLContent = loop.run_until_complete(wq_client.fetch(url))
        return html_content
    finally:
        loop.close()
