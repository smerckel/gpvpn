import asyncio
import argparse
import json
import logging
import sys

from . import server, message_processors, config
from .common import *

def server_app():
    logging.basicConfig(level=logging.WARNING)
    log_level = logging.DEBUG
    server.logger.setLevel(log_level)
    config.logger.setLevel(log_level)
    message_processors.logger.setLevel(log_level)
    cfg = config.GPVpnConfig().from_files()
    message_processor = message_processors.MessageProcessorVPNController(cfg)
    s = server.IPCServer(message_processor=message_processor)
    s.open()
    asyncio.run(s.run())


def client_app():    
    parser = argparse.ArgumentParser(prog='gpvpn',
                                     description='Global Connect VPN contoller',
                                     epilog='')
    parser.add_argument('command',
                        choices=['status', 's', 'connect', 'c', 'disconnect', 'd', 'stop_server'],
                        help='Commands to control the vpn status.')
    args = parser.parse_args()
    match args.command:
        case "status" | "s":
            s = COMMANDS.Status
        case "connect" | "c":
            s = COMMANDS.Open
        case "disconnect" | "d":
            s = COMMANDS.Close
        case "stop_server":
            s = COMMANDS.Quit
            
    command = args.command
    cfg = config.GPVpnAuthConfig()
    with server.IPCClient(cfg) as client:
        result = asyncio.run(client.send_request(s))
    return_code = result['return_code']
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
            if s == COMMANDS.Close:
                mesg = "VPN connection successfully deactivated"
            else:
                mesg = "VPN connection successfully activated"
        case RETURNCODES.Failed:
            if s == COMMANDS.Close:
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

                    
