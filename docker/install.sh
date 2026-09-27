#!/bin/bash
set -euo pipefail
CURRENT_DIR="$(pwd)"




update_kernel() {
  if [[ "$(uname -r)" == *cloud* ]]; then
    apt update
    uname -r
    apt install linux-image-amd64 -y
    cd /boot
    rm -rf *cloud*
    update-grub
    sudo rm -f /etc/modprobe.d/dirtyfrag.conf
    sudo depmod -a
    apt autoremove -y
    reboot
  fi
}

install_zsh() {
  if [[ "$SHELL" != */zsh ]]; then
      apt install zsh -y
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
  fi
}


install_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
  fi
}

vpnsetup() {
  apt update && apt upgrade -y
  apt install curl net-tools git wget htop btop vim -y
  update_kernel
  install_zsh
  install_docker

  cd "$CURRENT_DIR"
  if [ ! -d "$CURRENT_DIR/tmp" ]; then
    mkdir -p tmp && cd tmp
    git clone https://github.com/Ferrostol/tg_bot_vpn_l2.git
    cd tg_bot_vpn_l2
    git switch mode_to_docker_version #final
  fi
}

vpnsetup "$@"
