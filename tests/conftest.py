import pytest
import asyncio

from typing import Awaitable


@pytest.mark.asyncio # lets pytest know this is a coroutine
async def test_tasks(*tasks):
    return await asyncio.gather(*tasks)

@pytest.mark.asyncio 
async def run_awaitable_with_delay(task: Awaitable, delay: float) -> None:
    await asyncio.sleep(delay)
    return await task
