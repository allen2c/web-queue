import argparse
import time
import typing

import rich.console
import rich.progress
from huey.api import Result
from str_or_none import str_or_none

from web_queue.app import fetch_html, retrieve_result_as
from web_queue.client import Settings, WebQueueClient
from web_queue.types.fetch_html_message import FetchHTMLMessage, FetchHTMLMessageRequest
from web_queue.types.html_content import HTMLContent
from web_queue.types.message import MessageStatus

WAIT_FOR_SECONDS = 60

console = rich.console.Console()

wq_settings = Settings()
wq_client = WebQueueClient(wq_settings)


def main(url: str):
    # Enqueue
    task = typing.cast(
        Result,
        fetch_html(
            FetchHTMLMessage(data=FetchHTMLMessageRequest(url=url, headless=False))
        ),
    )
    console.print(f"[green]Task ID: {task.id}[/green]")

    # Tracking
    start_time = time.perf_counter()
    with rich.progress.Progress(
        rich.progress.BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        rich.progress.TimeRemainingColumn(),
        rich.progress.TextColumn("[progress.description]{task.description}"),
    ) as progress:
        progress_task = progress.add_task("Starting ...")
        while time.perf_counter() - start_time < WAIT_FOR_SECONDS:
            msg = wq_client.messages.retrieve_as(task.id, FetchHTMLMessage)
            if msg is not None:
                progress.update(
                    progress_task,
                    completed=msg.completed_steps,
                    total=msg.total_steps,
                    description=msg.message_text,
                )
            if msg.status in [MessageStatus.COMPLETED, MessageStatus.FAILED]:
                break
            time.sleep(0.5)

    if msg is None:
        console.print("[red]No queue message found[/red]")
        exit(1)

    # Retrieve result
    html_content = retrieve_result_as(task.id, HTMLContent)
    console.print("---")
    console.print(html_content.content)
    console.print("---")


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
