#!/bin/bash
set -euo pipefail
CURRENT_DIR="$(pwd)"
IMAGE_VPN="out_vpn_image"
CONTAINER_VPN="out_vpn_container"

VPN_IP="l2.checkpipipupu.tech"
VPN_USER="vpnlink"
VPN_PASSWORD="vpnlink"
VPN_PSK="vpn"




build_bot() {
  docker build -t "$IMAGE_VPN" -f docker/DockerfileOutVPN .
  cd "$CURRENT_DIR"
}

install_vpn() {
  cd "$CURRENT_DIR"
  if [ ! -d "$CURRENT_DIR/tmp" ]; then
    mkdir -p tmp && cd tmp
    git clone https://github.com/Ferrostol/tg_bot_vpn_l2.git
    cd tg_bot_vpn_l2
    git switch mode_to_docker_version #final
  fi
  cd "$CURRENT_DIR/tmp/tg_bot_vpn_l2"

  if ! docker image inspect "$IMAGE_VPN" >/dev/null 2>&1; then
    build_bot
  else
    docker image rm "$IMAGE_VPN"
    build_bot
  fi
  if docker ps --format '{{.Names}}' | grep -Fxq "$CONTAINER_VPN"; then
    docker kill "$CONTAINER_VPN"
  fi
  if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER_VPN"; then
    docker container rm "$CONTAINER_VPN"
  fi


  mkdir -p "$CURRENT_DIR/out_vpn"
  cd "$CURRENT_DIR/tmp/tg_bot_vpn_l2/config/vpn_client"

  cp xl2tpd.conf "$CURRENT_DIR/out_vpn/xl2tpd.conf"
  sed -i "s|VPN_IP|$VPN_IP|g" "$CURRENT_DIR/out_vpn/xl2tpd.conf"


  cp options.l2tpd.client "$CURRENT_DIR/out_vpn/options.l2tpd.client"
  sed -i "s|VPN_USER|$VPN_USER|g" "$CURRENT_DIR/out_vpn/options.l2tpd.client"
  sed -i "s|VPN_PASSWORD|$VPN_PASSWORD|g" "$CURRENT_DIR/out_vpn/options.l2tpd.client"


  cat > "$CURRENT_DIR/out_vpn/ipsec.secrets" <<EOF
%any  %any  : PSK "$VPN_PSK"
EOF

  cat > "$CURRENT_DIR/out_vpn/ipsec.conf" <<EOF
version 2.0

config setup
  ikev1-policy=accept
  virtual-private=%v4:10.0.0.0/8,%v4:192.168.0.0/16,%v4:172.16.0.0/12
  uniqueids=no
EOF
  cat client.conf >> "$CURRENT_DIR/out_vpn/ipsec.conf"
  sed -i "s|VPN_IP|$VPN_IP|g" "$CURRENT_DIR/out_vpn/ipsec.conf"

  cd "$CURRENT_DIR"
  docker run \
    --name "$CONTAINER_VPN" \
    --restart=always \
    -v "$CURRENT_DIR/out_vpn/xl2tpd.conf":/etc/xl2tpd/xl2tpd.conf \
    -v "$CURRENT_DIR/out_vpn/options.l2tpd.client":/etc/ppp/options.l2tpd.client \
    -v "$CURRENT_DIR/out_vpn/ipsec.secrets":/etc/ipsec.secrets \
    -v "$CURRENT_DIR/out_vpn/ipsec.conf":/etc/ipsec.conf \
    -d --privileged \
    "$IMAGE_VPN"
}

install_vpn "$@"