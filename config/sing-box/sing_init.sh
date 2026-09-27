#!/bin/bash
# 1. Создаем таблицу маршрутизации для TPROXY
ip rule add fwmark 1 table 400
ip route add local default dev lo table 400

# L2TP трафик
iptables -t mangle -A PREROUTING -s VPN_L2TP_NET/24 -p tcp -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1
iptables -t mangle -A PREROUTING -s VPN_L2TP_NET/24 -p udp -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1


# IKEV2 трафик
iptables -t mangle -A PREROUTING -s 192.168.43.0/24 -p tcp -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1
iptables -t mangle -A PREROUTING -s 192.168.43.0/24 -p udp -j TPROXY --on-port 12345 --on-ip 127.0.0.1 --tproxy-mark 1
