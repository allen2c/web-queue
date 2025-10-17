import functools
import typing

if typing.TYPE_CHECKING:
    from web_queue.client.config import Settings
    from web_queue.client.web import Web


class WebQueueClient:
    def __init__(self, settings: typing.Optional["Settings"] = None):
        from web_queue.client.config import Settings

        self.settings = settings or Settings()

    @functools.cached_property
    def web(self) -> "Web":
        from web_queue.client.web import Web

        return Web(self)
