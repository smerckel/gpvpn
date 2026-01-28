import enum

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

