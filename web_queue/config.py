import functools
import typing

import pydantic
import pydantic_settings
import yarl
from str_or_none import str_or_none

if typing.TYPE_CHECKING:
    from web_queue.client import WebQueueClient


class Settings(pydantic_settings.BaseSettings):
    WEB_QUEUE_NAME: str = pydantic.Field(default="web-queue")
    WEB_QUEUE_URL: pydantic.SecretStr = pydantic.SecretStr("")

    @pydantic.model_validator(mode="after")
    def validate_values(self) -> typing.Self:
        if str_or_none(self.WEB_QUEUE_NAME) is None:
            raise ValueError("WEB_QUEUE_NAME is required")
        if str_or_none(self.WEB_QUEUE_URL.get_secret_value()) is None:
            raise ValueError("WEB_QUEUE_URL is required")
        return self

    @functools.cached_property
    def web_queue_client(self) -> "WebQueueClient":
        from web_queue.client import WebQueueClient

        return WebQueueClient()

    @property
    def web_queue_safe_url(self) -> str:
        return str(yarl.URL(self.WEB_QUEUE_URL.get_secret_value()).with_password("***"))
