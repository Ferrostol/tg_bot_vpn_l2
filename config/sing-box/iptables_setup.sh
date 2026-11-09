#!/bin/bash


setup_l2tp_con() {
  USERS_FILE="/etc/ppp/chap-secrets"
  LOGIN="${PEERNAME:-}"
  USER_IP="${4:-}"
  INT="${1:-}"

  # 1. Проверим, что это не исходящий трафик
  if [ -n "$INT" ] && [ "$INT" == "vpn" ]; then
    exit 0
  fi

  # 2. Проверяем, есть ли логин в файле
  IN_FILE=0
  [ -n "$LOGIN" ] && grep -Eq "^\"${LOGIN}\".*#COMB" "$USERS_FILE" 2>/dev/null && IN_FILE=1

  # 3. Правила TPROXY для адреса пользователя
  if [ -n "$USER_IP" ]; then
    for proto in tcp udp; do
      RULE=(-s "$USER_IP" -p "$proto" -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1)

      if iptables -t mangle -C PREROUTING "${RULE[@]}" 2>/dev/null; then
        EXISTS=1
      else
        EXISTS=0
      fi

      if [ "$IN_FILE" -eq 1 ]; then
        # Логин в файле
        [ "$EXISTS" -eq 1 ] && iptables -t mangle -D PREROUTING "${RULE[@]}" 2>/dev/null || true
      else
        # Логин не в файле
        [ "$EXISTS" -eq 0 ] && iptables -t mangle -A PREROUTING "${RULE[@]}" 2>/dev/null || true
      fi
    done
  fi
}


setup_ipsec_con() {
  if [ -n "$PLUTO_PEER_CLIENT" ]; then
    for proto in tcp udp; do
      RULE=(-s "$PLUTO_PEER_CLIENT" -p "$proto" -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1)

      if iptables -t mangle -C PREROUTING "${RULE[@]}" 2>/dev/null; then
        EXISTS=1
      else
        EXISTS=0
      fi

      [ "$EXISTS" -eq 0 ] && iptables -t mangle -A PREROUTING "${RULE[@]}" 2>/dev/null || true
    done
  fi
}


main() {
  # Общая настройка сети - Создаем таблицу маршрутизации для TPROXY
  ip rule add fwmark 1 table 400 2>/dev/null || true
  ip route add local default dev lo table 400 2>/dev/null || true

  # Определим откуда был вызван скрипт:
  # - Переменная PEERNAME указывает на запуск из ip-up/ip-down.
  # - Переменная PLUTO_CONNECTION указывает на запуск из ipsec.

  # Запуск из ip-up/ip-down
  if [ -n "$PEERNAME" ]; then
    setup_l2tp_con $@
  fi

  # Запуск из ipsec
  if [ -n "$PLUTO_CONNECTION" ]; then
    setup_ipsec_con $@
  fi
}

main $@