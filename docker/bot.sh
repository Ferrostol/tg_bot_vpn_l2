#!/bin/bash
set -euo pipefail
CURRENT_DIR="$(pwd)"

BOT_IMAGE="my_bot_image"
BOT_CONTAINER="my_bot_container"


build_bot() {
  cd "$CURRENT_DIR"
  if [ ! -d "$CURRENT_DIR/tmp" ]; then
    mkdir -p tmp && cd tmp
    git clone https://github.com/Ferrostol/tg_bot_vpn_l2.git
    cd tg_bot_vpn_l2
    git switch mode_to_docker_version #final
  fi
  cd "$CURRENT_DIR/tmp/tg_bot_vpn_l2"

  docker build -t "$BOT_IMAGE" -f docker/DockerfileBot .
  cd "$CURRENT_DIR"
}


vpnsetup() {
  if ! docker image inspect "$BOT_IMAGE" >/dev/null 2>&1; then
    build_bot
  else
    docker image rm "$BOT_IMAGE"
    build_bot
  fi
  if docker ps --format '{{.Names}}' | grep -Fxq "$BOT_CONTAINER"; then
    docker kill "$BOT_CONTAINER"
  fi
  if docker ps -a --format '{{.Names}}' | grep -Fxq "$BOT_CONTAINER"; then
    docker container rm "$BOT_CONTAINER"
  fi
  mkdir -p "$CURRENT_DIR/bot"
  cat << EOF > "$CURRENT_DIR/bot/.env"
TOKEN=TOKEN
USE_VPN=Y
MULTI_CONNECT=Y
EOF
  touch "$CURRENT_DIR/bot/users.db"
  docker run \
    --name "$BOT_CONTAINER" \
    --env-file "$CURRENT_DIR/bot/.env" \
    --restart=always \
    -v "$CURRENT_DIR/bot/users.db":/app/others/users.db \
    -v "$CURRENT_DIR/vpn/ppp_connect.tdb":/app/others/ppp_connect.tdb \
    -v "$CURRENT_DIR/vpn/login_password_vpn":/app/others/login_password_vpn \
    -v "$CURRENT_DIR/vpn/ipsec_key.secrets":/app/ipsec_key.secrets \
    -v "$CURRENT_DIR/vpn/multi_connect.conf":/app/others/multi_connect.conf \
    -d --privileged \
    "$BOT_IMAGE"
}

vpnsetup "$@"