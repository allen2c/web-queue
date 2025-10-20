import typing

import pydantic
from str_or_none import str_or_none

from web_queue.types.message import Message


class FetchHTMLMessageRequest(pydantic.BaseModel):
    url: str
    headless: bool = False
    goto_timeout: int = 4000
    circling_times: int = 2
    scrolling_times: int = 3
    human_delay_base_delay: float = 1.2
    dynamic_content_loading_delay: float = 2

    @pydantic.model_validator(mode="after")
    def validate_url(self) -> typing.Self:
        if not str_or_none(self.url):
            raise ValueError("URL is required")
        return self


class FetchHTMLMessage(Message):
    data: FetchHTMLMessageRequest
