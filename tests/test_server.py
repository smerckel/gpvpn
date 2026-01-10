import pytest
import asyncio

from conftest import *

from gpvpn.server import IPCServer, IPCClient
from gpvpn.message_processors import MessageProcessorReverse

# conftest defines:
#    async def test_tasks(*tasks):
#    async def run_awaitable_with_delay(task: Awaitable, delay: float) -> None:

def test_open_server():
    server = IPCServer(message_processor=MessageProcessorReverse())
    server.open()
    server.close()

def test_reverse_server():
    server = IPCServer(message_processor=MessageProcessorReverse())
    server.open()
    with IPCClient() as client:
        result = asyncio.run(test_tasks(server.run(),
                                        run_awaitable_with_delay(client.send_request("hello"),
                                                                 delay=0.5),
                                        run_awaitable_with_delay(client.send_request("HELLO"),
                                                                 delay=0.6),
                                        run_awaitable_with_delay(server.stop(),
                                                                 delay=1)
                                        )
                             )
    assert result == [None, 'olleh', 'OLLEH', None]
