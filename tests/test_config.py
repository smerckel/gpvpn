import pytest
import os
import tempfile
from dataclasses import asdict

from gpvpn import config
from gpvpn.message_processors import MessageProcessorVPNController

TESTCONFIGTEXT=b"""lock_directory = lock_directory
log_directory = log_directory
lock_filename = lock_filename
log_filename = log_filename

vpnclient_path = /usr/bin/gpclient
"""
    

@pytest.fixture
def config_filename():
    with tempfile.NamedTemporaryFile(delete_on_close=False) as fp:
        fp.write(TESTCONFIGTEXT)
        fp.close()
        yield fp.name
    # removes the file at this stage

def test_config(config_filename):
    config_lines = TESTCONFIGTEXT.decode().split("\n")
    test_dict = {}
    for line in config_lines:
        kv  = [i.strip() for i in line.split("=")]
        if len(kv) == 2:
            k, v = kv
            test_dict[k] = v
    cnf = config.GPVpnConfig([config_filename])
    cnf.from_files()
    read_dict = asdict(cnf)
    for k,v in test_dict.items():
        assert read_dict[k] == v

def test_set_config_values(config_filename):
    cfg = config.GPVpnConfig([config_filename])
    mp = MessageProcessorVPNController(cfg)
    assert mp.lockfile == "lock_directory/lock_filename"
    assert mp.logfile == "log_directory/log_filename"
    assert mp.vpn_command == ['/usr/bin/gpclient', '--fix-openssl', 'connect', '--browser default', 'vpn.hereon.de']

def test_set_config_default_values():
    cfg = config.GPVpnConfig(["/tmp/not_EXISTING"])
    mp = MessageProcessorVPNController(cfg)
    assert mp.lockfile == "/var/run/gpclient.lock"
    assert mp.logfile == "/var/log/gpclient.log"
    assert mp.vpn_command == ['/usr/bin/gpclient', '--fix-openssl', 'connect', '--browser default', 'vpn.hereon.de']
    
