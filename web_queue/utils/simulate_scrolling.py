import random

import playwright.async_api
from typing_extensions import Literal


async def simulate_scrolling(
    page: playwright.async_api.Page,
    scroll_direction: Literal["down", "up"] | None = None,
    scroll_distance: int | None = None,
) -> None:
    scroll_direction = scroll_direction or random.choice(["down", "up"])
    scroll_distance = scroll_distance or random.randint(200, 800)
    if scroll_direction == "down":
        await page.mouse.wheel(0, scroll_distance)
    else:
        await page.mouse.wheel(0, -scroll_distance)
    return None
