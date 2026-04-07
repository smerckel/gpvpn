# GPVPN

## Introduction

GPVPN is a front-end to the open-source vpn client that is GlobalProtect compatible. The client can be found at
[GlobalProtect-openconnect](https://github.com/yuezk/GlobalProtect-openconnect).

This front-end allows the user to control the vpn connection from the command line. The system is based on a server-client model. The server (gpvpn_server) runs as root and creates and closes network devices used to in the vpn connection. The client engages with the (GlobalProtect) vpn server's authentication system. In a nutshell the following steps are implemented:

```
gpauth --fix-openssl --default-browser --gateway <vpn-server> | sudo
gpclient --fix-openssl connect --cookie-on-stdin --as-gateway
<vpn-server> 
```

See also issue #572 of [GlobalProtect-openconnect github repository](https://github.com/yuezk/GlobalProtect-openconnect).

## Installation

* First step is to install the GlobalProtect-openconnect client, see [here](https://github.com/yuezk/GlobalProtect-openconnect).
* Second step is to ensure a gpauth/gpclient combination, such as the one above, works. The option --fix-openssl may or may not be needed.
* Third step is to download and install the code in this repository (gpvpn)
  and install it using pip as *root*. This is needed because the server part is to be run as root.
* Fourth step is to create a group gpvpn and add the user who needs access to the vpn client to this group.

For example
```
sudo useradd gpvpn
```

```
sudo usermod -aG gpvpn <your login name>
```

Then logout and login, or reboot for the changes to take effect.


## Usage

In order to use the gpvpn client, the server must be started as root first.

To that end, create a configuration file, for example as /usr/local/etc/gpvpn/config.ini and populate the requirements with the options to gpclient as they worked, see example above.

```
lock_directory = /var/run
log_directory = /usr/local/var/log
lock_filename = gpclient.lock
log_filename = gpclient.log

vpnclient_path = /usr/bin/gpclient
vpnclient_options = --fix_openssl
vpnclient_command = connect
vpnclient_command_options = --browser default
vpnclient_url = gpp.<yourserver>
```
The lock_directory entry is the directory where gpclient creates its lock file.

Run the server (as root):

```
# gpvpn_server
```

Now create a config file for the gpvpn client, for example, $HOME/.config/gpvpn/config_auth.ini

```
vpnauth_path = /usr/bin/gpauth
vpnauth_options = --fix-openssl --default-browser --gateway
vpnauth_url = gpp.<yourserver>
```

and run the client as gpvpn.

The client takes one of 4 commands:

| Command     | Description                                                         |
|-------------|---------------------------------------------------------------------|
| status      | prints status of connection (inactive or active)                    |
| connect     | connects the vpn. You may have to sign in on a newly opened website |
| disconnect  | disconnects the vpn.                                                |
| quit_server | shuts down the server application                                   |


Furthermore, the client accepts the option -f to specify a configuration file in a non-standard location, and -v for increasing verbosity of the output. The option -vv for even more output.


