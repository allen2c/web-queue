import typing

import pydantic
import pydantic_settings
from str_or_none import str_or_none


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
