#!/bin/bash
# 1. Создаем таблицу маршрутизации для TPROXY
ip rule add fwmark 1 table 400 2>/dev/null || true
ip route add local default dev lo table 400 2>/dev/null || true


if ! iptables -t mangle -S PREROUTING | grep 12345; then
  # L2TP трафик
  iptables -t mangle -A PREROUTING -s VPN_L2TP_NET/24 -p tcp -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1 2>/dev/null || true
  iptables -t mangle -A PREROUTING -s VPN_L2TP_NET/24 -p udp -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1 2>/dev/null || true

  # IKEV2 трафик
  iptables -t mangle -A PREROUTING -s 192.168.43.0/24 -p tcp -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1 2>/dev/null || true
  iptables -t mangle -A PREROUTING -s 192.168.43.0/24 -p udp -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1 2>/dev/null || true
fi