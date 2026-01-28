#!/bin/bash

# Note timeout is the time the gpclient will run. It is not a real
# option, but allows us to set the idle time, which is useful for
# tests.

TIMEOUT=5

GPAUTH=gpauthMockup/gpauthMockUp
GPCLIENT=gpclientMockUp/gpclientMockUp

rm -rf /tmp/gpclient.lock

$GPAUTH --fix-openssl --default-browser --gateway gpp.hereon.de | $GPCLIENT --timeout=$TIMEOUT --fix-openssl connect --cookie-on-stdin --as-gateway gpp.hereon.de 
