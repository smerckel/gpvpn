from dataclasses import dataclass, field, fields, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Type, TypeVar
import configparser
import logging

T = TypeVar("T", bound="BaseConfig")
logger = logging.getLogger(__name__)

@dataclass
class BaseConfig:
    # locations checked in order; subclasses can override or extend
    config_paths: list = field(default_factory=lambda: [
        Path("/usr/local/etc/config.ini"),
        Path.home() / ".config" / "config.ini",
        Path.cwd() / "configuration.ini",
    ])

    def __post_init__(self):
        self.from_files()
        
    def from_files(self: Type[T], paths: Optional[Iterable[Path]] = None) -> T:
        """Instantiate config by reading INI-style key=value files in order."""
        search_paths = list(paths) if paths is not None else self.config_paths
        parser = configparser.ConfigParser()
        # treat file as a simple key=value no-section file by using DEFAULT section
        for p in map(Path, search_paths):
            if not p.exists():
                continue
            # read as a file with a [DEFAULT] wrapper so configparser can parse it
            text = p.read_text(encoding="utf-8")
            if not text.strip().startswith("["):
                text = "[DEFAULT]\n" + text
            parser.read_string(text)
            # apply values found to self (later files override earlier ones)
            for f in fields(self):
                name = f.name
                if name == "config_paths":
                    continue
                if parser.has_option("DEFAULT", name):
                    raw = parser.get("DEFAULT", name)
                    parsed = _coerce_type(raw, f.type, f.default)
                    setattr(self, name, parsed)
        return self

    def save(self, path: Path) -> None:
        p = Path(path)
        parser = configparser.ConfigParser()
        parser["DEFAULT"] = {k: _to_str(v) for k, v in asdict(self).items() if k != "config_paths"}
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as fh:
            parser.write(fh)

def _coerce_type(raw: str, typ: Any, default: Any) -> Any:
    """Simple coercion for common types used in config files."""
    # handle Optional[...] (very small heuristic)
    origin = getattr(typ, "__origin__", None)
    if origin is Optional:
        args = getattr(typ, "__args__", ())
        typ = args[0] if args else str

    # basic types
    if typ in (int,):
        try:
            return int(raw)
        except ValueError:
            return default
    if typ in (float,):
        try:
            return float(raw)
        except ValueError:
            return default
    if typ in (bool,):
        val = raw.strip().lower()
        if val in ("1", "true", "yes", "on"):
            return True
        if val in ("0", "false", "no", "off"):
            return False
        return default
    if typ in (list,):
        # naive comma-split
        return [s.strip() for s in raw.split(",") if s.strip()]
    # fallback to string
    return raw

def _to_str(val: Any) -> str:
    if isinstance(val, (list, tuple)):
        return ",".join(map(str, val))
    if val is None:
        return ""
    return str(val)



@dataclass
class GPVpnConfig(BaseConfig):
    # locations checked in order; subclasses can override or extend
    config_paths: list = field(default_factory=lambda: [
        Path("/usr/local/etc/gpvpn/config.ini"),
        Path.home() / ".config" / "gpvpn" / "config.ini",
        Path.cwd() / "config.ini",
    ])

    lock_directory: str = "/var/run"
    log_directory: str = "/var/log"
    lock_filename: str = "gpclient.lock"
    log_filename: str = "gpclient.log"

    vpnclient_path: str = "/usr/bin/gpclient"
    vpnclient_options: str = "--fix_openssl"
    vpnclient_command: str = "connect"
    vpnclient_command_options: str = "--browser default"
    vpnclient_url: str = "vpn.hereon.de"
