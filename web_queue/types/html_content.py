import logging

import pydantic

logger = logging.getLogger(__name__)


class HTMLContent(pydantic.BaseModel):
    title: str = pydantic.Field(default="")
    author: str = pydantic.Field(default="")
    chapter_id: str = pydantic.Field(default="")
    chapter_number: str = pydantic.Field(default="")
    content: str = pydantic.Field(default="")
    created_date: str = pydantic.Field(default="")
    updated_date: str = pydantic.Field(default="")

    # Private attributes
    _html: str = pydantic.PrivateAttr(default="")
