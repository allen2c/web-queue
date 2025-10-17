from web_queue.client import WebQueueClient


class Web:
    def __init__(self, client: WebQueueClient):
        self.client = client
