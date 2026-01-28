import enum
import json

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
    CommandNotUnderstood = enum.auto()
    
class ERRORCODES(enum.IntEnum):
    GroupError = enum.auto()

GROUPNAME = "gpvpn"

def serialise(function: typing.Callable) -> typing.Any:
    async def wrapper(*p) -> str:
        return_code = await function(*p)
        d = dict(return_code=return_code)
        return json.dumps(d)
    return wrapper

def deserialise(json_message) -> dict[str,str]:
    d = json.loads(json_message)
    return d
