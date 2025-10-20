import asyncio
import logging
import typing

import huey
import logfire
import logging_bullet_train as lbt
from huey.api import Task

import web_queue.config
from web_queue.types.message import MessageStatus

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
) -> typing.Optional[typing.Text]:
    from web_queue.types.fetch_html_message import FetchHTMLMessage

    message = FetchHTMLMessage.from_any(message)
    message.id = task.id
    message.status = MessageStatus.RUNNING

    wq_cache_key = web_queue_settings.get_message_cache_key(message.id)

    def update_message_cache(
        total_steps: int | None = None,
        completed_steps: int | None = None,
        message_text: str | None = None,
    ):
        if total_steps is not None:
            message.total_steps = total_steps
        if completed_steps is not None:
            message.completed_steps = completed_steps
        if message_text is not None:
            message.message = message_text
        web_queue_settings.message_cache.set(wq_cache_key, message.model_dump_json())

    logger.info(f"Fetching HTML with parameters: {message.data.model_dump_json()}")
    update_message_cache(message_text="Starting to fetch HTML...")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        wq_client: "WebQueueClient" = web_queue_settings.web_queue_client
        html_content: "HTMLContent" = loop.run_until_complete(
            wq_client.fetch(
                **message.data.model_dump(), step_callback=update_message_cache
            )
        )
        update_message_cache(100, 100, "Finished fetching HTML.")
        return html_content.model_dump_json()

    except Exception as e:
        logger.exception(e)
        logger.error(f"Failed to fetch HTML: {e}")
        update_message_cache(message_text=f"Failed to fetch HTML: {e}")

    finally:
        loop.close()

    return None
