import pytest
import asyncio

from typing import Awaitable


@pytest.mark.asyncio # lets pytest know this is a coroutine
async def test_tasks(*tasks):
    return_value = await asyncio.gather(*tasks)
    print("Test tasks completed")
    return return_value

@pytest.mark.asyncio 
async def run_awaitable_with_delay(task: Awaitable, delay: float) -> None:
    await asyncio.sleep(delay)
    return_value = await task
    print(f"task {task.__name__} is completed.")
    return return_value
