import asyncio
import argparse
import json
import logging
import sys

from . import server, message_processors
from .common import *

def server_app():
    logging.basicConfig(level=logging.WARNING)
    server.logger.setLevel(logging.DEBUG)
    message_processors.logger.setLevel(logging.DEBUG)
    message_processor = message_processors.MessageProcessorVPNController()
    s = server.IPCServer(message_processor=message_processor)
    s.open()
    asyncio.run(s.run())


def client_app():

    def decode(s:str) -> enum.Enum:
        s = s.strip('"').replace('\\"', '"')
        d = json.loads(s)
        v = d["return_code"]
        return RETURNCODES._value2member_map_[v]
    
    parser = argparse.ArgumentParser(prog='gpvpn',
                                     description='Global Connect VPN contoller',
                                     epilog='')
    parser.add_argument('command',
                        choices=['status', 'connect', 'disconnect', 'stop_server']
                        help='Commands to control the vpn status.')
    args = parser.parse_args()
    match args.command:
        case "status" | "s":
            s = "Status"
        case "connect" | "c":
            s = "Open"
        case "disconnect" | "d":
            s = "Close"
        case "stop_server":
            s = "Quit"
            
    command = args.command
    with server.IPCClient() as client:
        result = asyncio.run(client.send_request(command_str))
    return_code = decode(result)
    match return_code:
        case RETURNCODES.Active:
            mesg = "VPN connection is active"
        case RETURNCODES.Inactive:
            mesg = "VPN connection is inactive"
        case RETURNCODES.AlreadyConnected:
            mesg = "VPN connection is already active"
        case RETURNCODES.AlreadyDisconnected:
            mesg = "VPN connection is already inactive"
        case RETURNCODES.Success:
            if s == "Close":
                mesg = "VPN connection successfully deactivated"
            else:
                mesg = "VPN connection successfully activated"
        case RETURNCODES.Failed:
            if s == "Close":
                mesg = "VPN connection could not be deactivated"
            else:
                mesg = "VPN connection could not be activated"
        case RETURNCODES.QuitApplication:
            mesg = "gpvpn server killed"
        case RETURNCODES.CommandNotUnderstood:
            mesg = f"Command {args.command} was not understood. Try --help..."
        case _:
            mesg = "Received unknown return code from server"
    print(mesg)

                    
