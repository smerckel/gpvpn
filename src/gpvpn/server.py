import abc
import asyncio
import enum
import json
import logging
import typing
import os

import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)

class MessageProcessorBase(abc.ABC):

    @abc.abstractmethod
    async def process(self, message: str) -> str:
        ...

class MessageProcessorReverse(MessageProcessorBase):
    
    async def process(self, message: str) -> str:
        message = message[::-1]
        return message



    
        
class IPCServer:

    def __init__(self,
                 message_processor: MessageProcessorBase,
                 socket_path: str = '/tmp',
                 socket_name: str = 'ipcserver') -> None:
        self.message_processor = message_processor
        self.socket_path = socket_path
        self.socket_name = socket_name
        self.context : zmq.asyncio.Context
        self.socket : zmq.asyncio.Socket
        self.task : asyncio.Task
        logger.debug("Inited")
        
    def open(self) -> None:
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REP)
        # Using IPC: specify the IPC path
        path = os.path.join(os.path.abspath(self.socket_path),
                            self.socket_name)
        URL = f'ipc://{path}'
        self.socket.bind(URL)
        logger.debug("Opened")
        
    def close(self) -> None:
        self.socket.close()
        self.context.term()
        logger.debug("Closed")
        
    async def listen(self) -> None:
        logger.debug("Starting to listen...")
        while True:
            logger.debug("Waiting for message to arrive")
            recvd_message = await self.socket.recv_string()
            logger.info(f"Received request: {recvd_message}")
            return_message = await self.message_processor.process(recvd_message)
            # Send a reply back to the client
            await self.socket.send_string(f"Returning: {return_message}")
            
    async def run(self) -> None:
        logger.debug("Starting start...")
        self.task = asyncio.create_task(self.listen())
        logger.debug("Start started")
        try:
            await self.task            
        except asyncio.CancelledError:
            pass
        self.close()

    async def stop(self) -> None:
        if self.task.done():
            if self.task.cancelled():
                logger.warning("Trying to stop listen task, while it was already cancelled.")
            else:
                logger.warning("Trying to stop listen task that is already finished.")
        else:
            self.task.cancel()
            logger.debug("Stopping task...")



class Client:

    def __init__(self,
                 socket_path: str = '/tmp',
                 socket_name: str = 'ipcserver') -> None:
        self.socket_path = socket_path
        self.socket_name = socket_name
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REQ)

    def __enter__(self) -> typing.Self:
        self.open()
        return self
    
    def __exit__(self,
                 exc_type: typing.Any,
                 exc_value: typing.Any,
                 exc_traceback: typing.Any) -> None:
        self.close()
        
    def open(self):
        path = os.path.join(os.path.abspath(self.socket_path),
                            self.socket_name)
        URL = f'ipc://{path}'
        self.socket.connect(URL)
        
    def close(self) -> None:
        self.socket.close()
        self.context.term()
        logger.debug("Client Closed")

    async def send_request(self, message: str):
        await self.socket.send_string(message)
        # Wait for a reply
        reply = await self.socket.recv()
        print(f"Received reply: {reply.decode()}")


class COMMANDS(enum.IntEnum):
    Status = enum.auto()
    Open = enum.auto()
    Close  = enum.auto()
    Quit = enum.auto()

class RETURNCODES(enum.IntEnum):
    Active = enum.auto()
    Inactive = enum.auto()
    AlreadyConnected = enum.auto()
    AlreadyDisconnected = enum.auto()
    RunningWithoutSubprocess = enum.auto()
    Success = enum.auto()
    Failed = enum.auto()
    QuitApplication = enum.auto()

    
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
    async def check_status(self) -> dict[str, typing.Any]:
        # check whether lock file exists:
        if os.path.exists(self.lockfile): # Should we also analyse the output of route?
            return_code = RETURNCODES.Active
        else:
            return_code = RETURNCODES.Inactive
        d = dict(return_code=return_code)
        return d

    
    @serialise
    async def connect_vpn(self) -> enum.Enum:
        if os.path.exists(self.lockfile): # Should we also analyse the output of route?
            return RETURNCODES.AlreadyConnected
        self.subprocess = await self.run_detached_program(self.vpn_command)
        await asyncio.sleep(0.5)
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


        
            
if __name__ == "__main__":
    from typing import Awaitable
    import signal
    
    logging.basicConfig(level=logging.WARNING)
    logger.setLevel(logging.DEBUG)

    async def run_awaitable_with_delay(task: Awaitable, delay: float) -> None:
        logger.info(f"Scheduling task with a delay of {delay} seconds")
        await asyncio.sleep(delay)
        return await task

    async def test_tasks(*tasks):
        return await asyncio.gather(*tasks)

    async def run(limit):
        logger.debug(f"Starting run for {limit} seconds")
        for i in range(limit):
            await asyncio.sleep(1)
            logger.debug(f"Elapsed time: {i+1} s.")
        logger.debug(f"Coroutine run completed.")

    async def kill_from_lockfile(lockfile):
        try:
            with open(lockfile) as fp:
                pidstr = fp.readlines()
                pid = int(pidstr[0].strip())
                os.kill(pid, signal.SIGTERM)
        except FileNotFoundError:
            logger.debug(f"Could not find lockfile {lockfile}.")
            
    
    async def start_by_hand(command):
        process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.DEVNULL,  # Redirect stdout to nowhere
                stderr=asyncio.subprocess.DEVNULL,   # Redirect stderr to nowhere
            )
        return process

if 1:     
        message_processor = MessageProcessorVPNController()
        message_processor.vpn_command = ["../../gpclientMockUp/gpclientMockup"]
        message_processor.lockfile = "/tmp/gpclient.lock"

        if 1:
            # check, start_by_hand, check, kill, check, close
            result = asyncio.run(test_tasks(run(10),
                                            message_processor.process(json.dumps(COMMANDS.Status)),
                                            run_awaitable_with_delay(start_by_hand(message_processor.vpn_command), delay=2),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Status)), delay=4),
                                            run_awaitable_with_delay(kill_from_lockfile(message_processor.lockfile), delay=6),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Status)), delay=7),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Close)), delay=8),
                                            )
                                 )
            
        if 0:
            # check, start_by_hand, check, close
            result = asyncio.run(test_tasks(run(10),
                                            message_processor.process(json.dumps(COMMANDS.Status)),
                                            run_awaitable_with_delay(start_by_hand(message_processor.vpn_command), delay=2),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Status)), delay=4),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Close)), delay=6),
                                            )
                                 )
            
        
        if 0:
            # check, open, check, close, check.
            result = asyncio.run(test_tasks(run(10),
                                            message_processor.process(json.dumps(COMMANDS.Status)),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Open)), delay=2),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Status)), delay=4),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Close)), delay=6),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Status)), delay=8),
                                            )
                                 )
        if 0:
            # open, check, open, close, check close.
            result = asyncio.run(test_tasks(run(10),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Open)), delay=1),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Status)), delay=2),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Open)), delay=3),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Close)), delay=4),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Status)), delay=5),
                                            run_awaitable_with_delay(message_processor.process(json.dumps(COMMANDS.Close)), delay=6),
                                            )
                                 )
    
if 0:

        server = IPCServer(message_processor=MessageProcessorReverse())
        server.open()


        with Client() as client:
            asyncio.run(test_tasks(server.run(),
                                    run_awaitable_with_delay(client.send_request("hello"), delay=2),
                                    run_awaitable_with_delay(client.send_request("HELLO"), delay=3),
                                    run_awaitable_with_delay(server.stop(), delay=5)
                                    )
                        )
