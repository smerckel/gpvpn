import abc
import asyncio
import enum
import json
import logging
import typing
import os

import zmq
import zmq.asyncio

from .common import *

logger = logging.getLogger(__name__)

class MessageProcessorBase(abc.ABC):

    @abc.abstractmethod
    async def process(self, message: str) -> str:
        ...

class MessageProcessorReverse(MessageProcessorBase):
    
    async def process(self, message: str) -> str:
        message = message[::-1]
        return message


def serialise(function: typing.Callable) -> typing.Any:
    async def wrapper(*p) -> str:
        return_code = await function(*p)
        logger.debug(f"Message: {return_code}")
        d = dict(return_code=return_code)
        return json.dumps(d)
    return wrapper



class MessageProcessorVPNController(MessageProcessorBase):

    
    def __init__(self) -> None:
        self.lockfile = "/var/run/gpclient.lock"
        self.vpn_command = ["/usr/bin/gpclient",
                            "--fix-openssl",
                            "connect",
                            "--browser",
                            "default",
                            "vpn.hereon.de"]
        self.logfile = "gpclient.log"
        self.subprocess: asyncio.subprocess.Process | None = None

        
    def parse(self, message: str) -> enum.Enum:
        i = int(message)
        command = COMMANDS._value2member_map_[i]
        return command

    
    async def run_detached_program(self, command: list[str]) -> asyncio.subprocess.Process:
        # Create the subprocess in a new session
        with open(self.logfile, 'w') as fp:
            process = await asyncio.create_subprocess_exec(
                *command,
                #stdout=asyncio.subprocess.DEVNULL,  # Redirect stdout to nowhere
                #stderr=asyncio.subprocess.DEVNULL,   # Redirect stderr to nowhere
                stdout=fp,
                stderr=fp,
            )
        logger.info(f"Started detached process with PID: {process.pid}")
        return process

    
    @serialise
    async def check_status(self) -> enum.Enum:
        # check whether lock file exists:
        if os.path.exists(self.lockfile): # Should we also analyse the output of route?
            return_code = RETURNCODES.Active
        else:
            return_code = RETURNCODES.Inactive
        return return_code

    
    @serialise
    async def connect_vpn(self) -> enum.Enum:
        if os.path.exists(self.lockfile): # Should we also analyse the output of route?
            return RETURNCODES.AlreadyConnected
        self.subprocess = await self.run_detached_program(self.vpn_command)
        await asyncio.sleep(0.05) # is this long enough for gpclient program?
        if os.path.exists(self.lockfile): # Should we also analyse the output of route?
            return_code = RETURNCODES.Success
        else:
            return_code = RETURNCODES.Failed
        return return_code

    @serialise
    async def disconnect_vpn(self) -> enum.Enum:
        if not os.path.exists(self.lockfile):
            return RETURNCODES.AlreadyDisconnected
        if self.subprocess is None:
            # we have a running process possibly, but no
            # subprocess. Possibly started by hand. Kill it "manually"
            # too.
            return_code=RETURNCODES.RunningWithoutSubprocess
        else:
            self.subprocess.terminate()
            exit_code = await self.subprocess.wait()
            return_code=RETURNCODES.Success
        return return_code
            
    @serialise
    async def quit_application(self) -> enum.Enum:
        return RETURNCODES.QuitApplication
    
    async def process(self, message: str) -> str:
        command = self.parse(message)
        match command:
            case COMMANDS.Status:
                message = json.dumps(await self.check_status())
            case COMMANDS.Open:
                message = json.dumps(await self.connect_vpn())
            case COMMANDS.Close:
                message = json.dumps(await self.disconnect_vpn())
            case COMMANDS.Quit:
                message = json.dumps(await self.quit_application())
            case _:
                raise ValueError(f"Unknown command ({command}). Should not occur.")
        return message

    
