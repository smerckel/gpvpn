#!/bin/bash

# Installation script for gpvpn

GPAUTH=/usr/bin/gpauth
CONFIG_AUTH_DIR=$HOME/.config/gpvpn
CONFIG_DIR=/usr/local/etc/gpvpn
SYSTEMD_SERVICE_NAME=gpvpn.service
SYSTEMD_SERVICE_FILE_SOURCE_DIR=systemd
SYSTEMD_SERVICE_DIR=/etc/systemd/system

cat <<EOF
This script can be used to setup the gpvpn server. It will guide you thourgh the setup of the
configuration file of the gpvpn_server, as well as the configuration file of the gpvpn client.
Finally, you will get the option to install the start/stop control as a systemd service.

For some actions, you will need to assume root permission, and you
will be asked for your credentials accordingly.
EOF

if [ ! -f $GPAUTH ]; then
    echo
    echo "⚠️ Error!  🔥 💥"
    echo "The authentication program ${GPAUTH} is not installed."
    echo "Please install this first from https://github.com/yuezk/GlobalProtect-openconnect"
    exit 1
fi

if [ -z ${EDITOR:-} ]; then
    if [ -x /usr/bin/nano ]; then
	EDITOR=nano
    elif [ -x /usr/bin/gedit ]; then
	EDITOR=gedit
    elif [ -x /usr/bin/emacs ]; then
	EDITOR=emacs
    else
	echo
	echo "⚠️ Error! 🔥 💥"
	echo "Could not determine an editor. Set the environment variable EDITOR first and try again."
	exit 2
    fi
fi

## Write the gpvpn client config file

cat > tmpfile <<EOF
vpnauth_path = /usr/bin/gpauth
vpnauth_options= --fix-openssl --default-browser --gateway
vpnauth_url = gpp.hereon.de
EOF


$EDITOR tmpfile

read -r -p "Shall I copy your edits to a file config_auth.ini in $CONFIG_AUTH_DIR? [y/n]" answer
if [[ $answer =~ ^[yY]$ ]]; then
    mkdir -p $CONFIG_AUTH_DIR
    cp tmpfile ${CONFIG_AUTH_DIR}/config_auth.ini
else
    echo "⚠️ Skipping writing this file"
fi
rm tmpfile

## Write the gpvpn eserver config file


echo
echo "ℹ️ INFO: I am going to write the gpvpn server config file and may need sudo permsissions."
echo
n

read -p "Hit enter to continue."

cat > tmpfile <<EOF
[DEFAULT]
lock_directory = /var/run
log_directory = /var/log
lock_filename = gpclient.lock
log_filename = gpclient.log
vpnclient_path = /usr/bin/gpclient
vpnclient_options = --fix-openssl
vpnclient_command = connect
vpnclient_command_options = --cookie-on-stdin --as-gateway
vpnclient_url = gpp.hereon.de
EOF

$EDITOR tmpfile

read -r -p "Shall I copy your edits to a file config.ini in $CONFIG_DIR? [y/n]" answer
if [[ $answer =~ ^[yY]$ ]]; then
    sudo mkdir -p $CONFIG_AUTH_DIR
    sudo cp tmpfile ${CONFIG_AUTH_DIR}/config_auth.ini
else
    echo "⚠️ Skipping writing this file"
fi
rm tmpfile

## Install systemd service

read -r -p "Shall I install a systemd service to start gpvpn_server automatically? [y/n]" answer
if [[ $answer =~ ^[yY]$ ]]; then
    sudo cp ${SYSTEMD_SERVICE_FILE_SOURCE_DIR}/${SYSTEMD_SERVICE_NAME} ${SYSTEMD_SERVICE_DIR}
    sudo systemctl daemon-reload                                                                                                             
    sudo systemctl enable --now "${SYSTEMD_SERVICE_NAME%.service}"
else
    echo "⚠️ Skipping systemd installation."
fi
echo "Installation completed."
