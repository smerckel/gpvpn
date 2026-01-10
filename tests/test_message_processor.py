import pytest
import asyncio
import signal
from typing import Awaitable
import os
import json

from gpvpn.message_processors import MessageProcessorVPNController
from gpvpn.common import *

# import some common functions and fixtures:
from conftest import *
# conftest defines:
#    async def test_tasks(*tasks):
#    async def run_awaitable_with_delay(task: Awaitable, delay: float) -> None:

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

def encode(cmd:enum.Enum) -> s:
    return json.dumps(cmd)

def decode(s:str) -> enum.Enum:
    s = s.strip('"').replace('\\"', '"')
    d = json.loads(s)
    v = d["return_code"]
    return RETURNCODES._value2member_map_[v]


@pytest.fixture
def message_processor():
    mp = MessageProcessorVPNController()
    mp.vpn_command = ["gpclientMockUp/gpclientMockup"]
    mp.lockfile = "/tmp/gpclient.lock"
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

def test_start_stop(message_processor):
    p = [run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Open)), delay=0.1),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Status)), delay=0.2),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Close)), delay=0.3),
         ]
    r = asyncio.run(test_tasks(*p))
    result = [decode(i) for i in r if not i is None]
    assert result == [RETURNCODES.Success, RETURNCODES.Active, RETURNCODES.Success]

def test_stop(message_processor):
    r = asyncio.run(message_processor.process(encode(COMMANDS.Close)))
    result = decode(r)
    assert result == RETURNCODES.AlreadyDisconnected

    
def test_start_start_stop(message_processor):
    p = [run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Open)), delay=0.0),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Open)), delay=0.1),
         run_awaitable_with_delay(message_processor.process(encode(COMMANDS.Close)), delay=0.2),
         ]
    r = asyncio.run(test_tasks(*p))
    result = [decode(i) for i in r if not i is None]
    assert result == [RETURNCODES.Success, RETURNCODES.AlreadyConnected, RETURNCODES.Success]

def test_quite_server(message_processor):
    r = asyncio.run(message_processor.process(encode(COMMANDS.Quit)))
    result = decode(r)
    assert result == RETURNCODES.QuitApplication
