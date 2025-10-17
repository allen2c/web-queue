import asyncio
import random


async def human_delay(
    base_delay: float = 1.2, *, jitter_range: tuple[float, float] = (0.5, 1.5)
) -> None:
    jitter = random.uniform(jitter_range[0], jitter_range[1])
    total_delay = base_delay + jitter
    await asyncio.sleep(total_delay)
    return None
