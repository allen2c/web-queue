import functools
import typing

if typing.TYPE_CHECKING:
    from web_queue.client.ai import AI
    from web_queue.client.clean import Clean
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

    @functools.cached_property
    def clean(self) -> "Clean":
        from web_queue.client.clean import Clean

        return Clean(self)

    @functools.cached_property
    def ai(self) -> "AI":
        from web_queue.client.ai import AI

        return AI(self)
