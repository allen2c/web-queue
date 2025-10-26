import typing

import fastapi

from web_queue.client import WebQueueClient
from web_queue.types.message import Message, MessageStatus, MessageVar


class Messages:
    def __init__(self, client: WebQueueClient):
        self.client = client

    def get(self, message_id: str) -> typing.Optional[str]:
        message_cache_key = self.get_cache_key(message_id)
        maybe_json = self.client.settings.message_cache.get(message_cache_key)
        if maybe_json is None:
            return None
        return maybe_json

    def retrieve(self, message_id: str) -> str:
        json_data = self.get(message_id)
        if json_data is None:
            raise fastapi.HTTPException(status_code=404, detail="Message not found")
        return json_data

    def retrieve_as(self, message_id: str, type: typing.Type[MessageVar]) -> MessageVar:
        json_data = self.retrieve(message_id)
        return type.model_validate_json(json_data)

    def set(self, message_id: str, message: Message) -> None:
        message_cache_key = self.get_cache_key(message_id)
        self.client.settings.message_cache.set(
            message_cache_key, message.model_dump_json()
        )

    def update(
        self,
        message_id: str,
        *,
        message_text: typing.Optional[str] = None,
        data: typing.Optional[typing.Any] = None,
        status: typing.Optional[MessageStatus] = None,
        total_steps: typing.Optional[int] = None,
        completed_steps: typing.Optional[int] = None,
        error: typing.Optional[str] = None,
    ) -> Message:
        message = self.retrieve_as(message_id, Message)
        if message_text is not None:
            message.message_text = message_text
        if data is not None:
            message.data = data
        if status is not None:
            message.status = status
        if total_steps is not None:
            message.total_steps = total_steps
        if completed_steps is not None:
            message.completed_steps = completed_steps
        if error is not None:
            message.error = error
        self.set(message_id, message)

        return message

    def wrap_update_message(
        self, message_id: str, message: Message
    ) -> typing.Callable[..., None]:
        def _update(
            message_text: typing.Optional[str] = None,
            data: typing.Optional[typing.Any] = None,
            status: typing.Optional[MessageStatus] = None,
            total_steps: typing.Optional[int] = None,
            completed_steps: typing.Optional[int] = None,
            error: typing.Optional[str] = None,
        ) -> None:
            if message_text is not None:
                message.message_text = message_text
            if data is not None:
                message.data = data
            if status is not None:
                message.status = status
            if total_steps is not None:
                message.total_steps = total_steps
            if completed_steps is not None:
                message.completed_steps = completed_steps
            if error is not None:
                message.error = error
            self.set(message_id, message)

        return _update

    def get_cache_key(self, message_id: str) -> str:
        return f"{self.client.settings.WEB_QUEUE_NAME}:message:{message_id}"
