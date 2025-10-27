import asyncio
import logging
import typing

import huey
import logfire
import logging_bullet_train as lbt
from huey.api import Task

from web_queue.client import Settings, WebQueueClient
from web_queue.types.fetch_html_message import FetchHTMLMessage
from web_queue.types.html_content import HTMLContent
from web_queue.types.message import MessageStatus, MessageUpdate

lbt.set_logger("web_queue")

logfire.configure()
logfire.instrument_openai()

logger = logging.getLogger(__name__)

logger.info("Web queue app starting...")

wq_settings = Settings()
wq_client = WebQueueClient(wq_settings)
logger.info(f"Web queue connecting to redis: {wq_settings.web_queue_safe_url}")

huey_app = huey.RedisExpireHuey(
    wq_settings.WEB_QUEUE_NAME,
    url=wq_settings.WEB_QUEUE_URL.get_secret_value(),
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

    global wq_client

    message = FetchHTMLMessage.from_any(message)
    message.id = task.id
    message.status = MessageStatus.RUNNING

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    update_message_func = wq_client.messages.wrap_update_message(message.id, message)

    try:
        logger.info(f"Fetching HTML with parameters: {message.data.model_dump_json()}")
        update_message_func(
            MessageUpdate(
                total_steps=100,
                completed_steps=0,
                status=MessageStatus.RUNNING,
                message_text="Starting to fetch HTML...",
            )
        )

        html_content: "HTMLContent" = loop.run_until_complete(
            wq_client.fetch(
                **message.data.model_dump(), step_callback=update_message_func
            )
        )

        update_message_func(
            MessageUpdate(
                total_steps=100,
                completed_steps=100,
                status=MessageStatus.COMPLETED,
                message_text="Finished fetching HTML.",
            )
        )

        return html_content.model_dump_json()

    except Exception as e:
        logger.exception(e)
        logger.error(f"Failed to fetch HTML: {e}")
        update_message_func(
            MessageUpdate(
                total_steps=100,
                completed_steps=100,
                status=MessageStatus.FAILED,
                message_text=f"Failed to fetch HTML: {e}",
            )
        )

    finally:
        loop.close()

    return None
