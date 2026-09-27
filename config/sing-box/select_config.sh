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
    cp /CURRENT_DIR/tg_bot_vpn_l2/config/sing-box/config_$NEW.json /etc/sing-box/config.json
    systemctl restart sing-box
fi

if [ "$NEW" = "eth0" ]; then
    echo "d vpn" > /var/run/xl2tpd/l2tp-control
    ipsec down l2tp-client
    ipsec up l2tp-client
    echo "c vpn" > /var/run/xl2tpd/l2tp-control
    sleep 2
fi