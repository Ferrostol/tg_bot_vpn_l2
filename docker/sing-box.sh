#!/bin/bash
set -euo pipefail
CURRENT_DIR="$(pwd)"
IMAGE_BOX="ghcr.io/sagernet/sing-box:v1.14.2"
CONTAINER_BOX="sing_box_container"



install_box() {
  cd "$CURRENT_DIR"
  if [ ! -d "$CURRENT_DIR/tmp" ]; then
    mkdir -p tmp && cd tmp
    git clone https://github.com/Ferrostol/tg_bot_vpn_l2.git
    cd tg_bot_vpn_l2
    git switch mode_to_docker_version #final
  fi

  if ! docker image inspect "$IMAGE_BOX" >/dev/null 2>&1; then
    docker pull "$IMAGE_BOX"
  fi
  if docker ps --format '{{.Names}}' | grep -Fxq "$CONTAINER_BOX"; then
    docker kill "$CONTAINER_BOX"
  fi
  if docker ps -a --format '{{.Names}}' | grep -Fxq "$CONTAINER_BOX"; then
    docker container rm "$CONTAINER_BOX"
  fi

  mkdir -p "$CURRENT_DIR/sing-box"
  cp "$CURRENT_DIR/tmp/tg_bot_vpn_l2/config/sing-box/config_eth0.json" "$CURRENT_DIR/sing-box"
  docker run -d \
    --name="$CONTAINER_BOX" \
    --restart=always \
    --network=host \
    --cap-add=NET_ADMIN \
    --cap-add=NET_RAW \
    -v "$CURRENT_DIR/sing-box":/etc/sing-box/ \
    "$IMAGE_BOX" \
    -D /var/lib/sing-box \
    -C /etc/sing-box/ run
}

install_box "$@"
