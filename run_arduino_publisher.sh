#!/bin/bash

PASSWORD=$1
PROXY=$2

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )/../tcp-proxy"
while true; do /usr/bin/python3 -m tcp_proxy.private localhost:5000 4578 $PROXY $PASSWORD ; sleep 1; done &

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
/usr/bin/python3 -m arduino_publisher.web 
