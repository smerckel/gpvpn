import asyncio
import logging
import typing
import os

import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)


class IPCServer:

    def __init__(self,
                 socket_path: str = '/tmp',
                 socket_name: str = 'ipcserver') -> None:
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
            message = await self.socket.recv_string()
            logger.info(f"Received request: {message}")
            # Send a reply back to the client
            await self.socket.send_string(f"Hello, {message}")
            
    async def run(self) -> None:
        logger.debug("Starting start...")
        self.task = asyncio.create_task(self.listen())
        logger.debug("Start started")

        for i in range(5):
            logger.debug("sleep")
            await asyncio.sleep(1)
        self.task.cancel()            
        try:
            await self.task            
        except asyncio.CancelledError:
            pass

        
if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    logger.setLevel(logging.DEBUG)
    
    server = IPCServer()
    server.open()
    asyncio.run(server.run())
