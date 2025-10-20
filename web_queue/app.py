import asyncio
import logging
import typing

import huey
import logfire
import logging_bullet_train as lbt
from huey.api import Task

import web_queue.config

if typing.TYPE_CHECKING:
    from web_queue.client import WebQueueClient
    from web_queue.types.fetch_html_message import FetchHTMLMessage
    from web_queue.types.html_content import HTMLContent

lbt.set_logger("web_queue")

logfire.configure()
logfire.instrument_openai()

logger = logging.getLogger(__name__)

logger.info("Web queue app starting...")

web_queue_settings = web_queue.config.Settings()
logger.info(f"Web queue connecting to redis: {web_queue_settings.web_queue_safe_url}")

huey_app = huey.RedisExpireHuey(
    web_queue_settings.WEB_QUEUE_NAME,
    url=web_queue_settings.WEB_QUEUE_URL.get_secret_value(),
    expire_time=24 * 60 * 60,  # 24 hours
)


@huey_app.task(
    retries=1,
    retry_delay=8,
    expires=24 * 60 * 60,
    context=True,
)
def fetch_html(
    message: typing.Union["FetchHTMLMessage", str, bytes], task: Task
) -> str:
    from web_queue.types.fetch_html_message import FetchHTMLMessage

    message = FetchHTMLMessage.from_any(message)
    message.id = task.id

    logger.info(f"Fetching HTML from {message.data.url}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        wq_client: "WebQueueClient" = web_queue_settings.web_queue_client
        html_content: "HTMLContent" = loop.run_until_complete(
            wq_client.fetch(**message.data.model_dump())
        )
        return html_content.model_dump_json()

    finally:
        loop.close()
