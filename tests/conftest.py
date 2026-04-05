import pytest
import asyncio

from typing import Awaitable

from gpvpn.server import IPCClient
from gpvpn.message_processors import MessageProcessorVPNController
from gpvpn.config import GPVpnConfig

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



class IPCClientMockUp(IPCClient):
    def __init__(self):
        super().__init__()
        # Override auth command with a mocked up version
        self.auth_command = ["gpauthMockup/gpauthMockUp",
                             "--fix-openssl",
                             "--default-browser",
                             "--gateway",
                             "gpp.hereon.de"]

class MessageProcessorVPNControllerWithTimeout(MessageProcessorVPNController):
    def __init__(self, timeout=1):
        cfg = GPVpnConfig(["tests/mockup.ini"])
        cfg.vpnclient_options=" ".join([f"--timeout={timeout}", *cfg.vpnclient_options])
        super().__init__(cfg)
        self.WAIT_FOR_LOCKFILE=0.5
