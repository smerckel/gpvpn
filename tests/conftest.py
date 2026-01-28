import pytest
import asyncio

from typing import Awaitable

from gpvpn.server import IPCClient
from gpvpn.message_processors import MessageProcessorVPNController

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
        super().__init__()
        self.set_vpn_command(2)
        self.lockfile = "/tmp/gpclient.lock"
        self.WAIT_FOR_LOCKFILE=0.5

    def set_vpn_command(self, timeout):
        self.vpn_command = ["gpclientMockUp/gpclientMockUp",
                            f"--timeout={timeout}", # sets "working time to 1 second" Option not available in real client.
                            "--fix-openssl",
                            "connect",
                            "--cookie-on-stdin",
                            "--as-gateway",
                            "gpp.hereon.de"]
        
    def set_timeout(self, timeout):
        self.set_vpn_command(timeout)
