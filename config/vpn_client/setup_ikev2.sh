#!/bin/bash
set -e
exit
DEF=$(ip -4 route show default | grep -v ipsec | head -n1)
[ -n "$DEF" ] || { echo "no default route yet" >&2; exit 1; }

# Таблица 200: копия основной таблицы без маршрутов ipsec1
ip route flush table 200 2>/dev/null || true
ip -4 route show table main \
  | grep -v -E '^(default|0\.0\.0\.0/1|128\.0\.0\.0/1)' \
  | grep -v ipsec \
  | while read -r r; do ip route replace $r table 200 || true; done
ip route replace $DEF table 200

# Правила: сначала трафик, привязанный к ipsec1, затем всё остальное
ip rule del pref 80 2>/dev/null || true
ip rule del pref 90 2>/dev/null || true
ip rule add pref 80 oif ipsec1 lookup main
ip rule add pref 90 lookup 200




# Проверка
#ip rule del pref 79