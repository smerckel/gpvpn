import abc
import asyncio
import enum
import json
import logging
import typing
import os
import stat
import sys
import grp

import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)

from .message_processors import MessageProcessorBase
from .common import GROUPNAME, ERRORCODES, COMMANDS

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
        if os.getuid() == 0: # called as root
            # set the permssion correctly rw for ug
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP)
            # Get the GID for the group 'gpvpn'
            try:
                group_info = grp.getgrnam(GROUPNAME)
            except KeyError:
                logger.error(f"Groupname {GROUPNAME} is not available.")
                sys.exit(1)
            gid = group_info.gr_gid
            # Set the group of the socket file
            os.chown(path, -1, gid)  # -1 to keep the current owner
        logger.info(f"gpvpn server serving at {URL}.")
        
    def close(self) -> None:
        self.socket.close()
        self.context.term()
        logger.info("gpvpn server shut down.")
        
    async def listen(self) -> None:
        logger.debug("Starting to listen...")
        while True:
            logger.debug("Waiting for message to arrive")
            recvd_message = await self.socket.recv_string()
            logger.info(f"Received request: {recvd_message}")
            return_message = await self.message_processor.process(recvd_message)
            # Send a reply back to the client
            await self.socket.send_string(return_message)
            
    async def run(self) -> None:
        logger.info("Listening for incomming connections...")
        self.task = asyncio.create_task(self.listen())
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



class IPCClient:
    def __init__(self,
                 socket_path: str = '/tmp',
                 socket_name: str = 'ipcserver') -> None:
        self.socket_path = socket_path
        self.socket_name = socket_name
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.groupname = GROUPNAME
        self.auth_command = ["/usr/bin/gpauth",
                             "--fix-openssl",
                             "--default-browser",
                             "--gateway",
                             "gpp.hereon.de"]
        
    def __enter__(self) -> typing.Self:
        self.verify_in_group()
        self.open()
        return self
    
    def __exit__(self,
                 exc_type: typing.Any,
                 exc_value: typing.Any,
                 exc_traceback: typing.Any) -> None:
        self.close()

    def verify_in_group(self) -> bool:
        try:
            gpvpn_group = grp.getgrnam(self.groupname)
        except KeyError:
            logger.error(f"There is no group {self.groupname} defined.")
            sys.exit(ERRORCODES.GroupError)
        whoIam = os.getlogin()
        return_value = whoIam in gpvpn_group.gr_mem
        if not return_value:
            logger.error(f"User {whoIam} is not in {self.groupname}.")
            sys.exit(ERRORCODES.GroupError)
        return return_value
            
    def open(self):
        path = os.path.join(os.path.abspath(self.socket_path),
                            self.socket_name)
        URL = f'ipc://{path}'
        self.socket.connect(URL)
        
    def close(self) -> None:
        self.socket.close()
        self.context.term()
        logger.debug("Client Closed")

    async def authenticate(self):
        process = await asyncio.create_subprocess_exec(
            *self.auth_command,
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.DEVNULL)
        stdout, stderr = await process.communicate()
        return stdout

    async def send_request(self, message: str) -> str:
        d = dict(command_code=message)
        if message == COMMANDS.Open:
            bmessage = await self.authenticate()
            logincode = bmessage.decode()
            d["logincode"] = logincode
        logger.debug(f"Dictionary to pass on: {d}")
        json_message = json.dumps(d)
        await self.socket.send_string(json_message)
        logger.debug("Waiting for reply from server...")
        # Wait for a reply
        reply = await self.socket.recv()
        logger.debug(f"Reply from server: {reply}.")
        return reply.decode()


    


