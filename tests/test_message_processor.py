import pytest
import asyncio
import signal
from typing import Awaitable
import os
import json

from gpvpn.message_processors import MessageProcessorVPNController
from gpvpn.common import *

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

# import some common functions and fixtures:
from conftest import *
# conftest defines:
#    async def test_tasks(*tasks):
#    async def run_awaitable_with_delay(task: Awaitable, delay: float) -> None:

@pytest.fixture
def logincode():
    # output of gpauthMockUp exe.
    s = '{"success":{"portalUserauthcookie":"","preloginCookie":"HyiL+E5lbwtah/vkSYDaJ0AZfAk+GLJIEjmjrXvnfNn3v1eDS+cgDY7NbjvwZjb28WQQeQ==","token":null,"username":"lucas.merckelbach@hereon.de"}}'
    return s

@pytest.mark.asyncio
async def run(limit):
    print(f"Starting run for {limit} seconds")
    for i in range(limit):
        await asyncio.sleep(1)
        print(f"Elapsed time: {i+1} s.")
    print(f"Coroutine run completed.")

@pytest.mark.asyncio
async def kill_from_lockfile(lockfile):
    try:
        with open(lockfile) as fp:
            pidstr = fp.readlines()
            pid = int(pidstr[0].strip())
            os.kill(pid, signal.SIGTERM)
    except FileNotFoundError:
        print(f"Could not find lockfile {lockfile}.")

@pytest.mark.asyncio
async def start_by_hand(command):
    process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.DEVNULL,  # Redirect stdout to nowhere
            stderr=asyncio.subprocess.DEVNULL,   # Redirect stderr to nowhere
        )
    return process

def encode(cmd:enum.Enum, login_code:str="") -> s:
    d = dict(command_code=cmd)
    if login_code:
        d["logincode"] = login_code
    return json.dumps(d)

def decode(s:str) -> enum.Enum:
    s = s.strip('"').replace('\\"', '"')
    d = json.loads(s)
    v = d["return_code"]
    for code, value in RETURNCODES.__members__.items():
        if value==v:
            return_code = value
            break
    return return_code


@pytest.fixture
def message_processor():
    mp = MessageProcessorVPNControllerWithTimeout()
    try:
        os.unlink(mp.lockfile)
    except FileNotFoundError:
        pass
    return mp

def test_construct_message_processor(message_processor):
    assert os.path.exists(message_processor.vpn_command[0])

def test_verify_subprocess_is_not_running(message_processor):
    m = encode(COMMANDS.Status)
    s = asyncio.run(message_processor.process(m))
    result = decode(s)
    assert result == RETURNCODES.Inactive

def test_start(message_processor, logincode):
    message_processor.set_timeout(1)
    p = [run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Open, logincode)), delay=0.1),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Status)), delay=0.2),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Status)), delay=1.5),
         ]
    r = asyncio.run(test_tasks(*p))
    result = [decode(i) for i in r if not i is None]
    assert result == [RETURNCODES.Success, RETURNCODES.Active, RETURNCODES.Inactive]

    
def test_start_stop_already_disconnected(message_processor, logincode):
    message_processor.set_timeout(1)
    p = [run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Open, logincode)), delay=0.1),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Status)), delay=0.2),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Close)), delay=2),
         ]
    r = asyncio.run(test_tasks(*p))
    result = [decode(i) for i in r if not i is None]
    assert result == [RETURNCODES.Success, RETURNCODES.Active, RETURNCODES.AlreadyDisconnected]


def test_start_stop(message_processor, logincode):
    message_processor.set_timeout(20)
    p = [run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Open, logincode)), delay=0.1),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Status)), delay=0.2),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Close)), delay=2),
         ]
    r = asyncio.run(test_tasks(*p))
    result = [decode(i) for i in r if not i is None]
    assert result == [RETURNCODES.Success, RETURNCODES.Active, RETURNCODES.Success]

    
def test_start_start_stop(message_processor, logincode):
    message_processor.set_timeout(20)
    p = [run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Open, logincode)), delay=0.1),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Open, logincode)), delay=0.2),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Close)), delay=2),
         ]
    r = asyncio.run(test_tasks(*p))
    result = [decode(i) for i in r if not i is None]
    assert result == [RETURNCODES.Success, RETURNCODES.AlreadyConnected, RETURNCODES.Success]

def test_quit_server(message_processor):
    r = asyncio.run(message_processor.process(encode(COMMANDS.Quit)))
    result = decode(r)
    assert result == RETURNCODES.QuitApplication
