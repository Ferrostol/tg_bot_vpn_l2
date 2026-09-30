#!/bin/bash
set -euo pipefail
CURRENT_DIR="$(pwd)"
IMAGE_VPN="hwdsl2/ipsec-vpn-server"
CONTAINER_VPN="ipsec-vpn-server"

PSK_KEY="vpn"
USERNAME_LOGIN="main"
USERNAME_PASSWORD="vpn"
VPN_L2TP_NET="10.1.0.0/16"
VPN_L2TP_LOCAL="10.1.0.1"
VPN_L2TP_POOL="10.1.0.10-10.1.254.254"
DOMAIN="mode.checkpipipupu.tech"


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
    docker pull "$IMAGE_VPN"
  fi
  if docker ps --format '{{.Names}}' | grep -Fxq "$CONTAINER_VPN"; then
    docker kill "$CONTAINER_VPN"
  fi
  if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER_VPN"; then
    docker container rm "$CONTAINER_VPN"
  fi
  mkdir -p "$CURRENT_DIR/vpn"
  cat << EOF > "$CURRENT_DIR/vpn/.env"
VPN_IPSEC_PSK="$PSK_KEY"
VPN_USER="$USERNAME_LOGIN"
VPN_PASSWORD="$USERNAME_PASSWORD"
VPN_DNS_NAME="$DOMAIN"
VPN_L2TP_NET="$VPN_L2TP_NET"
VPN_L2TP_LOCAL="$VPN_L2TP_LOCAL"
VPN_L2TP_POOL="$VPN_L2TP_POOL"
EOF
  mkdir -p "$CURRENT_DIR/vpn/ikev2"

  touch "$CURRENT_DIR/vpn/ppp_connect.tdb"
  touch "$CURRENT_DIR/vpn/login_password_vpn"
  touch "$CURRENT_DIR/vpn/ipsec_key.secrets"
  touch "$CURRENT_DIR/vpn/multi_connect.conf"
  echo "yes" > "$CURRENT_DIR/vpn/multi_connect.conf"
  cp "$CURRENT_DIR/tmp/tg_bot_vpn_l2/config/vpn_server/ip-up" "$CURRENT_DIR/vpn/ip-up"
  chmod +x "$CURRENT_DIR/vpn/ip-up"
  sed -i '1i#!/bin/bash' "$CURRENT_DIR/vpn/ip-up"
  cp "$CURRENT_DIR/tmp/tg_bot_vpn_l2/config/vpn_server/ip-down" "$CURRENT_DIR/vpn/ip-down"
  chmod +x "$CURRENT_DIR/vpn/ip-down"
  sed -i '1i#!/bin/bash' "$CURRENT_DIR/vpn/ip-down"

  docker run \
    --name "$CONTAINER_VPN" \
    --network=host \
    --env-file "$CURRENT_DIR/vpn/.env" \
    --restart=always \
    -v "$CURRENT_DIR/vpn/ikev2":/etc/ipsec.d \
    -v "$CURRENT_DIR/vpn/ppp_connect.tdb":/var/run/pppd2.tdb \
    -v "$CURRENT_DIR/vpn/login_password_vpn":/etc/ppp/chap-secrets \
    -v "$CURRENT_DIR/vpn/ipsec_key.secrets":/etc/ipsec.secrets \
    -v "$CURRENT_DIR/vpn/multi_connect.conf":/etc/ppp/multi_connect.conf \
    -v "$CURRENT_DIR/vpn/ip-up":/etc/ppp/ip-up \
    -v "$CURRENT_DIR/vpn/ip-down":/etc/ppp/ip-down \
    -v /lib/modules:/lib/modules:ro \
    -d --privileged \
    hwdsl2/ipsec-vpn-server
}

install_vpn "$@"
