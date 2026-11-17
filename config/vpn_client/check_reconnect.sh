#!/bin/bash
OLD=$(cat $STATE_FILE 2>/dev/null)

INTERFACE="vpn"
TARGET="1.1.1.1"
COUNT=2
TIMEOUT=1


reconnect() {
  echo "d vpn" > /var/run/xl2tpd/l2tp-control
  sleep 3
  echo "c vpn" > /var/run/xl2tpd/l2tp-control
  sleep 10
}

sleep 4
if ! ping -I "$INTERFACE" -c "$COUNT" -W "$TIMEOUT" "$TARGET" >/dev/null 2>&1; then
  if ip link show dev "$INTERFACE" 2>/dev/null | grep -q "state UNKNOWN"; then
    sleep 5
    if ! ping -I "$INTERFACE" -c "$COUNT" -W "$TIMEOUT" "$TARGET" >/dev/null 2>&1; then
      reconnect
    fi
  else
    reconnect
  fi
fi