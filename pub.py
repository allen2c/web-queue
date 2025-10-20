import argparse
import time
import typing

from huey.api import Result
from str_or_none import str_or_none

from web_queue.app import fetch_html
from web_queue.types.fetch_html_message import FetchHTMLMessage, FetchHTMLMessageRequest

WAIT_FOR_SECONDS = 60


def main(url: str):
    task = fetch_html(FetchHTMLMessage(data=FetchHTMLMessageRequest(url=url)))
    task = typing.cast(Result, task)
    print(f"Task ID: {task.id}")

    start_time = time.perf_counter()
    while time.perf_counter() - start_time < WAIT_FOR_SECONDS:
        result: str | None = task.get(blocking=False)  # type: ignore
        if result is not None:
            break
        time.sleep(0.1)

    print(type(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str)
    args = parser.parse_args()

    might_url = str_or_none(args.url)
    if might_url is None:
        print(f"Invalid URL: {args.url}")
        exit(1)
    url = might_url

    main(url)
