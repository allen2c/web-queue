import asyncio
import math
import random
import typing

import playwright.async_api
from playwright._impl._api_structures import ViewportSize

Number: typing.TypeAlias = float | int


async def simulate_mouse_circling(
    page: playwright.async_api.Page,
    default_viewport_size: ViewportSize | None = None,
    *,
    start_position: tuple[Number, Number] | None = None,
) -> tuple[Number, Number]:
    _viewport_size = (
        page.viewport_size
        or default_viewport_size
        or ViewportSize(width=1920, height=1080)
    )

    # Random starting position
    if start_position:
        start_x = start_position[0]
        start_y = start_position[1]
    else:
        start_x = random.randint(100, _viewport_size["width"] - 100)
        start_y = random.randint(100, _viewport_size["height"] - 100)
    center_x = start_x + 100
    center_y = start_y + 100
    radius = 50
    x = center_x
    y = center_y

    # Simulate smooth circle: Move to multiple points
    for angle in range(0, 360, 60):  # Every 30 degrees a point
        rad = (angle * 3.14159) / 180
        x = center_x + radius * random.uniform(0.8, 1.2) * random.choice([-1, 1]) * abs(
            math.cos(rad)
        )
        y = center_y + radius * random.uniform(0.8, 1.2) * random.choice([-1, 1]) * abs(
            math.sin(rad)
        )
        await page.mouse.move(x, y, steps=random.randint(10, 20))  # Smooth movement
        await asyncio.sleep(random.uniform(0.01, 0.05))  # Tiny delay

    return (x, y)
