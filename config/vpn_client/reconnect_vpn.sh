#!/bin/bash

if ! ping -I vpn 1.1.1.1 -c 2 -W 1 >/dev/null 2>&1; then
    echo "d vpn" > /var/run/xl2tpd/l2tp-control
    ipsec down l2tp-client >/dev/null
    sleep 5
    ipsec up l2tp-client >/dev/null
    echo "c vpn" > /var/run/xl2tpd/l2tp-control
    sleep 5
    echo "reconnect"
fi