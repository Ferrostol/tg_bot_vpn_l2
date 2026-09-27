#!/bin/bash
STATE_FILE=/run/singbox_if

if ping -I vpn 1.1.1.1 -c 2 -W 1 >/dev/null 2>&1; then
    NEW=vpn
else
    NEW=eth0
fi

OLD=$(cat $STATE_FILE 2>/dev/null)

if [ "$NEW" != "$OLD" ]; then
    echo $NEW > $STATE_FILE
    cat /etc/sing-box-all/config_$NEW.json > /etc/sing-box/config.json
    kill 1
fi

exit 0