import pytest
import asyncio
import logging
import os
import grp

from conftest import *

from gpvpn.server import IPCServer, IPCClient
from gpvpn.message_processors import MessageProcessorReverse
from gpvpn.common import *


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("gpvpn.server")
logger.setLevel(logging.DEBUG)

# conftest.py defines:
#    async def test_tasks(*tasks):
#    async def run_awaitable_with_delay(task: Awaitable, delay: float) -> None:

def test_open_server():
    server = IPCServer(message_processor=MessageProcessorReverse())
    server.open()
    server.close()

# Mock up class disabling verify_in_group check.
class IPCClientNoCheck(IPCClient):
    def verify_in_group(self) -> bool:
        return True

class IPCClientMockUp(IPCClient):
    def __init__(self):
        super().__init__()
        # Override auth command with a mocked up version
        self.auth_command = ["gpauthMockup/gpauthMockUp",
                             "--fix-openssl",
                             "--default-browser",
                             "--gateway",
                             "gpp.hereon.de"]


def test_reverse_server():
    server = IPCServer(message_processor=MessageProcessorReverse())
    server.open()
    with IPCClientNoCheck() as client:
        result = asyncio.run(test_tasks(server.run(),
                                        run_awaitable_with_delay(client.send_request("hello"),
                                                                 delay=0.5),
                                        run_awaitable_with_delay(client.send_request("HELLO"),
                                                                 delay=0.6),
                                        run_awaitable_with_delay(server.stop(),
                                                                 delay=1)
                                        )
                             )
    expected_result = [None, {"return_command": "olleh"}, {"return_command": "OLLEH"}, None]
    assert result == expected_result


def test_ipcclient_non_existing_group():
    with pytest.raises(SystemExit):
        client = IPCClient()
        client.groupname = "non-existent"
        client.verify_in_group()

def test_ipcclient_not_in_group():
        client = IPCClient()
        uid = os.getuid()
        if uid == 0:
            print("Nothing to test here.")
            # we are root, nothing to test.
            assert True
        else:
            # any user is not in group  root 
            client.groupname = "root"
        with pytest.raises(SystemExit):
            client.verify_in_group()

def test_ipcclient_in_group():
        client = IPCClient()
        uid = os.getuid()
        gids = os.getgroups()
        client.groupname = grp.getgrgid(gids[0]).gr_name
        if uid == 0:
            print("Nothing to test here.")
            # we are root, nothing to test.
            assert True
        else:
            assert client.verify_in_group()


def test_ipcclient_run_server():
    message_processor = MessageProcessorVPNControllerWithTimeout()
    message_processor.set_timeout(1)
    server = IPCServer(message_processor=message_processor)
    server.open()
    with IPCClientMockUp() as client:
        result = asyncio.run(test_tasks(server.run(),
                                        run_awaitable_with_delay(server.stop(),
                                                                 delay=2)
                                        )
                             )
    assert result == [None, None]

def test_ipcclient_status():
    message_processor = MessageProcessorVPNControllerWithTimeout()
    message_processor.set_timeout(1)
    server = IPCServer(message_processor=message_processor)
    server.open()
    with IPCClientMockUp() as client:
        result = asyncio.run(test_tasks(server.run(),
                                        run_awaitable_with_delay(client.send_request(COMMANDS.Status),
                                                                 delay=0.5),
                                        run_awaitable_with_delay(server.stop(),
                                                                 delay=2)
                                        )
                             )
    assert result == [None, {'return_code': 2}, None]

    
def test_ipcclient_auth():
    message_processor = MessageProcessorVPNControllerWithTimeout()
    message_processor.set_timeout(1)
    server = IPCServer(message_processor=message_processor)
    server.open()
    with IPCClientMockUp() as client:
        result = asyncio.run(test_tasks(server.run(),
                                        run_awaitable_with_delay(client.send_request(COMMANDS.Open),
                                                                 delay=0.5),
                                        run_awaitable_with_delay(server.stop(),
                                                                 delay=3)
                                        )
                             )
    assert result[0] == result[2] == None
    assert result[1]["return_code"] == RETURNCODES.Success

    
