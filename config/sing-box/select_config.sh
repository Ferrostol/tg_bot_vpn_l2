#!/bin/bash

INTERFACE_ETH0="eth0"
INTERFACE_L2TP="vpn"
INTERFACE_IKEV2="ipsec1"
TARGET="1.1.1.1"
COUNT=2
TIMEOUT=1

STATE_FILE=/run/singbox_if
TMT=$(cat $STATE_FILE 2>/dev/null)
OLD=${TMT:-$INTERFACE_ETH0}

check_exist_int() {
  if ip link show dev "$1" 2>/dev/null | grep -q "state UNKNOWN"; then
    echo "1"
  else
    echo "0"
  fi
}

ping_int() {
  if ping -I "$1" -c "$COUNT" -W "$TIMEOUT" "$TARGET" >/dev/null 2>&1; then
    echo "1"
  else
    echo "0"
  fi
}

if [ "$OLD" == "$INTERFACE_ETH0" ]; then
  if [[ $(ping_int "$INTERFACE_IKEV2") -eq 1 ]]; then
    NEW="$INTERFACE_IKEV2"
  else
    if [[ $(ping_int "$INTERFACE_L2TP") -eq 1 ]]; then
      NEW="$INTERFACE_L2TP"
    else
      NEW="$OLD"
    fi
  fi
fi

if [ "$OLD" == "$INTERFACE_IKEV2" ]; then
  if [[ $(ping_int "$INTERFACE_IKEV2") -eq 1 ]]; then
    NEW="$OLD"
  else
    sleep 2
    if [[ $(ping_int "$INTERFACE_IKEV2") -eq 1 ]]; then
      NEW="$OLD"
    elif [[ $(ping_int "$INTERFACE_L2TP") -eq 1 ]]; then
      NEW="$INTERFACE_L2TP"
    else
      NEW="$INTERFACE_ETH0"
    fi
  fi
fi

if [ "$OLD" == "$INTERFACE_L2TP" ]; then
  if [[ $(ping_int "$INTERFACE_L2TP") -eq 1 ]]; then
    NEW="$OLD"
  elif [[ $(ping_int "$INTERFACE_IKEV2") -eq 1 ]]; then
    NEW="$INTERFACE_IKEV2"
  else
    NEW="$INTERFACE_ETH0"
  fi
fi
echo "2" >> /etc/sing-box/test.txt

if [ "$NEW" != "$OLD" ]; then
  echo $NEW > $STATE_FILE
  if [ "$NEW" == "$INTERFACE_ETH0" ]; then
    cat /etc/sing-box/config_eth0.json > /etc/sing-box/config.json
  else
    cat /etc/sing-box/config_route.json > /etc/sing-box/config.json
    sed -i "s|ETH_INTERFACE|$NEW|g" /etc/sing-box/config.json
  fi
  kill 1
fi

exit 0