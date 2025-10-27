import time
import typing

import fastapi

from web_queue.client import WebQueueClient
from web_queue.types.message import Message, MessageStatus, MessageUpdate, MessageVar


class Messages:
    def __init__(self, client: WebQueueClient):
        self.client = client

    def get(self, message_id: str, *, timeout: float = 10.0) -> typing.Optional[str]:
        ts = time.perf_counter()
        while time.perf_counter() - ts < timeout:
            message_cache_key = self.get_cache_key(message_id)
            maybe_json = self.client.settings.message_cache.get(message_cache_key)
            if maybe_json is not None:
                break
            else:
                time.sleep(0.1)

        if maybe_json is None:
            return None
        return maybe_json

    def retrieve(self, message_id: str, *, timeout: float = 10.0) -> str:
        json_data = self.get(message_id, timeout=timeout)
        if json_data is None:
            raise fastapi.HTTPException(status_code=404, detail="Message not found")
        return json_data

    def retrieve_as(
        self, message_id: str, model: typing.Type[MessageVar], *, timeout: float = 10.0
    ) -> MessageVar:
        json_data = self.retrieve(message_id, timeout=timeout)
        return model.model_validate_json(json_data)

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
    ) -> typing.Callable[[MessageUpdate], None]:
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

    def poll_util_done(
        self,
        message_id: str,
        *,
        timeout: float = 60.0,
        model: typing.Type[MessageVar],
        delay: float = 0.2,
    ) -> MessageVar:
        ts = time.perf_counter()
        msg: MessageVar | None = None

        while is_timeout := (time.perf_counter() - ts < timeout):
            msg = self.retrieve_as(message_id, model)
            if msg.status in [MessageStatus.COMPLETED, MessageStatus.FAILED]:
                break
            time.sleep(delay)

        if msg is None:
            raise fastapi.HTTPException(status_code=404, detail="Message not found")

        if is_timeout:
            raise fastapi.HTTPException(
                status_code=408, detail="Timeout waiting for message to be done"
            )

        return msg

    def get_cache_key(self, message_id: str) -> str:
        return f"{self.client.settings.WEB_QUEUE_NAME}:message:{message_id}"
