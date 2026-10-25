#!/bin/bash
STATE_FILE=/run/singbox_if
OLD=$(cat $STATE_FILE 2>/dev/null)

INTERFACE="vpn"
TARGET="1.1.1.1"
COUNT=2
TIMEOUT=1

# Первичная попытка пинга через указанный интерфейс.
if ping -I "$INTERFACE" -c "$COUNT" -W "$TIMEOUT" "$TARGET" >/dev/null 2>&1; then
    NEW=vpn
else
    if [ "$OLD" = "eth0" ]; then
        NEW=eth0
    else
        if ip link show dev "$INTERFACE" 2>/dev/null | grep -q "state UNKNOWN"; then
            sleep 5
            if ping -I "$INTERFACE" -c "$COUNT" -W "$TIMEOUT" "$TARGET" >/dev/null 2>&1; then
                NEW=vpn
            else
                NEW=eth0
            fi
        else
            NEW=eth0
        fi
    fi
fi


if [ "$NEW" != "$OLD" ]; then
    echo $NEW > $STATE_FILE
    cat /etc/sing-box-all/config_$NEW.json > /etc/sing-box/config.json
    kill 1
fi

exit 0