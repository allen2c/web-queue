import enum
import json
import typing

import pydantic


class MessageStatus(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Message(pydantic.BaseModel):
    id: str | None = None
    data: typing.Any
    status: MessageStatus = pydantic.Field(default=MessageStatus.PENDING)
    total_steps: int = pydantic.Field(default=100)
    completed_steps: int = pydantic.Field(default=0)
    error: typing.Optional[str] = pydantic.Field(default=None)

    @classmethod
    def from_any(cls, any: typing.Union[pydantic.BaseModel, typing.Dict, str, bytes]):
        if isinstance(any, pydantic.BaseModel):
            return cls.model_validate_json(any.model_dump_json())
        elif isinstance(any, typing.Dict):
            return cls.model_validate_json(json.dumps(any))
        elif isinstance(any, str):
            return cls.model_validate_json(any)
        elif isinstance(any, bytes):
            return cls.model_validate_json(any)
        else:
            raise ValueError(f"Invalid type: {type(any)}")
