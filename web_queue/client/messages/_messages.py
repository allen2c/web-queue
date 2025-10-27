import typing

import fastapi

from web_queue.client import WebQueueClient
from web_queue.types.message import Message, MessageUpdate, MessageVar


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
        message_update: MessageUpdate,
    ) -> Message:
        message = self.retrieve_as(message_id, Message)
        if message_update.message_text is not None:
            message.message_text = message_update.message_text
        if message_update.data is not None:
            message.data = message_update.data
        if message_update.status is not None:
            message.status = message_update.status
        if message_update.total_steps is not None:
            message.total_steps = message_update.total_steps
        if message_update.completed_steps is not None:
            message.completed_steps = message_update.completed_steps
        if message_update.error is not None:
            message.error = message_update.error
        self.set(message_id, message)

        return message

    def wrap_update_message(
        self, message_id: str, message: Message
    ) -> typing.Callable[..., None]:
        def _update(message_update: MessageUpdate) -> None:
            if message_update.message_text is not None:
                message.message_text = message_update.message_text
            if message_update.data is not None:
                message.data = message_update.data
            if message_update.status is not None:
                message.status = message_update.status
            if message_update.total_steps is not None:
                message.total_steps = message_update.total_steps
            if message_update.completed_steps is not None:
                message.completed_steps = message_update.completed_steps
            if message_update.error is not None:
                message.error = message_update.error
            self.set(message_id, message)

        return _update

    def get_cache_key(self, message_id: str) -> str:
        return f"{self.client.settings.WEB_QUEUE_NAME}:message:{message_id}"
