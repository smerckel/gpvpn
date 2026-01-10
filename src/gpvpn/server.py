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

from .message_processors import MessageProcessorBase

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
            await self.socket.send_string(return_message)
            
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



class IPCClient:

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

    async def send_request(self, message: str) -> str:
        await self.socket.send_string(message)
        # Wait for a reply
        reply = await self.socket.recv()
        return reply.decode()


    


