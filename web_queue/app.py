import huey

from web_queue.config import Settings

web_queue_settings = Settings()
huey = huey.RedisHuey(
    web_queue_settings.WEB_QUEUE_NAME,
    url=web_queue_settings.WEB_QUEUE_URL.get_secret_value(),
)


@huey.task(retries=1, retry_delay=8)
def add_numbers(a, b):
    return a + b
