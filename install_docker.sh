#!/bin/bash
set -euo pipefail
CURRENT_DIR="$(pwd)"

BRANCH="final"

# Дополнительные функции
prompt_until_nonempty() {
  local var_name="$1"
  local prompt_text="$2"
  local default_v="$3"
  local input=""

  while [ -z "${!var_name:-}" ]; do
    read -rp "$prompt_text [$default_v]: " input
    if [ -n "$input" ]; then
      export "$var_name"="$input"
    else
      export "$var_name"="$default_v"
    fi
  done
}

prompt_until_nonempty_yn() {
  local var_name="$1"
  local prompt_text="$2"
  local default_v="$3"
  local input=""

  while [[ -z "${!var_name:-}" || ! "${!var_name:-}" =~ ^[YyNn]$ ]]; do
    read -rp "$prompt_text (Y/N)[$default_v]? " input
    if [ -n "$input" ]; then
      export "$var_name"="$input"
    else
      export "$var_name"="$default_v"
    fi
  done
}

# Получение конфигов для запуска
configure_vars() {
  prompt_until_nonempty_yn SYSTEM_SETUP "Выполнить базовую настройку системы?" "Y"
  prompt_until_nonempty_yn MIDDLE_SERVER "Текущий сервер является промежуточным?" "Y"

  prompt_until_nonempty DOMAIN "Введите домен для текущего сервера" ""
  prompt_until_nonempty_yn MULTI_CONNECT "Разрешить одновременные подключения к VPN" "Y"

  prompt_until_nonempty USERNAME_LOGIN "Введите имя пользователя создаваемого VPN (USERNAME_LOGIN)" "login"
  prompt_until_nonempty USERNAME_PASSWORD "Введите пароль пользователя создаваемого VPN (USERNAME_PASSWORD)" "password"
  prompt_until_nonempty PSK_KEY "Введите PSK_KEY (Pre-Shared Key)(PSK_KEY)" "psk"

  if [[ "${MIDDLE_SERVER}" =~ ^[Yy]$ ]]; then
    prompt_until_nonempty VPN_L2TP_NET "Укажите подсеть (VPN_L2TP_NET)" "10.1.0.0"
    export VPN_L2TP_LOCAL="${VPN_L2TP_NET%.*}.1"
    export VPN_L2TP_POOL="${VPN_L2TP_NET%.*}.10-${VPN_L2TP_NET%.*}.254"
    prompt_until_nonempty VPN_IP "Введите IP конечного VPN (VPN_IP)" "localhost"
    prompt_until_nonempty VPN_USER "Введите имя пользователя конечного VPN (VPN_USER)" "login"
    prompt_until_nonempty VPN_PASSWORD "Введите пароль конечного VPN (VPN_PASSWORD)" "password"
    export VPN_PSK="$PSK_KEY"
  else
    prompt_until_nonempty VPN_L2TP_NET "Укажите подсеть (VPN_L2TP_NET)" "192.168.42.0"
    export VPN_L2TP_LOCAL="${VPN_L2TP_NET%.*}.1"
    export VPN_L2TP_POOL="${VPN_L2TP_NET%.*}.10-${VPN_L2TP_NET%.*}.254"
  fi

  prompt_until_nonempty_yn INSTALL_BOT "Выполнять ли установку бота на текущий сервер?" "Y"
  if [[ "${INSTALL_BOT}" =~ ^[Yy]$ ]]; then
    prompt_until_nonempty BOT_TOKEN "Введите Telegram bot token (BOT_TOKEN)" "NONE"
    prompt_until_nonempty USE_VPN "Использовать vpn для бота" "Y"
  fi
}


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

uninstall() {
  if [[ -f /etc/my_vpn_server ]]; then
    echo "Удаляем уже установленную программу"
    curl -fsSL "https://raw.githubusercontent.com/Ferrostol/tg_bot_vpn_l2/refs/heads/$BRANCH/docker/uninstall.sh" | bash
    echo "Программа удалена"
  fi
}

clone_git() {
  cd "$CURRENT_DIR"
  if [ ! -d "$CURRENT_DIR/tg_bot_vpn_l2" ]; then
    git clone https://github.com/Ferrostol/tg_bot_vpn_l2.git
    cd tg_bot_vpn_l2
    git switch "$BRANCH"
    mkdir -p "$CURRENT_DIR/tg_bot_vpn_l2/others"
  fi
}

init_compose_file() {
  cd "$CURRENT_DIR/tg_bot_vpn_l2"
  cat << EOF > ./others/docker-compose.yaml
services:

EOF
}

setup_vpn() {
  #setup vpn
  mkdir -p "$CURRENT_DIR/vpn"
  cat << EOF > "$CURRENT_DIR/vpn/.env"
VPN_IPSEC_PSK="$PSK_KEY"
VPN_USER="$USERNAME_LOGIN"
VPN_PASSWORD="$USERNAME_PASSWORD"
VPN_DNS_NAME="$DOMAIN"
VPN_L2TP_NET="$VPN_L2TP_NET/16"
VPN_L2TP_LOCAL="$VPN_L2TP_LOCAL"
VPN_L2TP_POOL="$VPN_L2TP_POOL"
EOF
  mkdir -p "$CURRENT_DIR/vpn/ikev2"
  touch "$CURRENT_DIR/vpn/ppp_connect.tdb"
  touch "$CURRENT_DIR/vpn/login_password_vpn"
  touch "$CURRENT_DIR/vpn/ipsec_key.secrets"
  [[ "$MULTI_CONNECT" =~ ^[Yy]$ ]] && echo "yes" > "$CURRENT_DIR/vpn/multi_connect.conf"
  [[ "$MULTI_CONNECT" =~ ^[Nn]$ ]] && echo "no"  > "$CURRENT_DIR/vpn/multi_connect.conf"

  cd "$CURRENT_DIR/tg_bot_vpn_l2/"
  cp ./config/vpn_server/ip-up "$CURRENT_DIR/vpn/ip-up"
  chmod +x "$CURRENT_DIR/vpn/ip-up"
  sed -i '1i#!/bin/bash' "$CURRENT_DIR/vpn/ip-up"
  cp ./config/vpn_server/ip-down "$CURRENT_DIR/vpn/ip-down"
  chmod +x "$CURRENT_DIR/vpn/ip-down"
  sed -i '1i#!/bin/bash' "$CURRENT_DIR/vpn/ip-down"

  touch ./others/iptables_setup.sh
  echo "/opt/src/iptables_setup.sh" >> "$CURRENT_DIR/vpn/ip-up"


  if [[ "$MIDDLE_SERVER" =~ ^[Yy]$ ]]; then
    sed 's/DOCKER_FILE_VPN/DockerfileAllVPN/g' ./docker/composeVPN.yaml >> ./others/docker-compose.yaml
  else
    sed 's/DOCKER_FILE_VPN/DockerfileOnlyVPN/g' ./docker/composeVPN.yaml >> ./others/docker-compose.yaml
  fi
}

setup_middle_server() {
  if [[ "$MIDDLE_SERVER" =~ ^[Nn]$ ]]; then
    return
  fi
  #setup sing-box
  mkdir -p "$CURRENT_DIR/sing-box"
  cd "$CURRENT_DIR/tg_bot_vpn_l2/config/"
  cp ./sing-box/config_eth0.json "$CURRENT_DIR/sing-box/config.json"
  cp ./sing-box/select_config.sh "$CURRENT_DIR/sing-box/select_config.sh"
  chmod +x "$CURRENT_DIR/sing-box/select_config.sh"
  cat ./sing-box/sing_init.sh >> ../others/iptables_setup.sh
  sed -i "s|VPN_L2TP_NET|${VPN_L2TP_NET}|g" ../others/iptables_setup.sh

  #setup out_vpn
  mkdir -p "$CURRENT_DIR/vpn/xl2tpd_config"
  cd "$CURRENT_DIR/tg_bot_vpn_l2/config/vpn_client"
  cp xl2tpd.conf "$CURRENT_DIR/vpn/xl2tpd_config/xl2tpd.conf"
  sed -i "s|VPN_IP|$VPN_IP|g" "$CURRENT_DIR/vpn/xl2tpd_config/xl2tpd.conf"
  sed -i "s|/etc/ppp/|/etc/xl2tpd/configs/|g" "$CURRENT_DIR/vpn/xl2tpd_config/xl2tpd.conf"
  cp options.l2tpd.client "$CURRENT_DIR/vpn/xl2tpd_config/options.l2tpd.client"
  sed -i "s|VPN_USER|$VPN_USER|g" "$CURRENT_DIR/vpn/xl2tpd_config/options.l2tpd.client"
  sed -i "s|VPN_PASSWORD|$VPN_PASSWORD|g" "$CURRENT_DIR/vpn/xl2tpd_config/options.l2tpd.client"
  cat client.conf >> "$CURRENT_DIR/vpn/ikev2/ipsec.conf"
  sed -i "s|VPN_IP|$VPN_IP|g" "$CURRENT_DIR/vpn/ikev2/ipsec.conf"

  cd "$CURRENT_DIR/tg_bot_vpn_l2/"
  cat ./docker/composeSingBox.yaml >> ./others/docker-compose.yaml
}

setup_bot() {
  if [[ "$INSTALL_BOT" =~ ^[Nn]$ ]]; then
    return
  fi
  #setup bot
  mkdir -p "$CURRENT_DIR/bot"
  echo "TOKEN=$BOT_TOKEN" > "$CURRENT_DIR/bot/.env"
  echo "USE_VPN=$USE_VPN" >> "$CURRENT_DIR/bot/.env"
  [[ "$MULTI_CONNECT" =~ ^[Yy]$ ]] && echo "MULTI_CONNECT=Y" >> "$CURRENT_DIR/bot/.env"
  [[ "$MULTI_CONNECT" =~ ^[Nn]$ ]] && echo "MULTI_CONNECT=N"  >> "$CURRENT_DIR/bot/.env"
  touch "$CURRENT_DIR/bot/users.db"

  cd "$CURRENT_DIR/tg_bot_vpn_l2/"
  cat ./docker/composeBot.yaml >> ./others/docker-compose.yaml
}

start_docker() {
  cd "$CURRENT_DIR/tg_bot_vpn_l2"
  sed -i "s|/CURRENT_DIR/|$CURRENT_DIR/|g" ./others/docker-compose.yaml
  cat << EOF >> ./others/docker-compose.yaml
networks:
  my:
EOF
  docker compose -f ./others/docker-compose.yaml up -d
}

vpnsetup() {
  configure_vars
  if [[ "$SYSTEM_SETUP" =~ ^[Yy]$ ]]; then
    apt update && apt upgrade -y
    apt install curl net-tools git wget htop btop vim -y
  fi
  update_kernel
  install_zsh
  install_docker
  uninstall
  echo "$CURRENT_DIR" > /etc/my_vpn_server
  clone_git
  init_compose_file
  setup_vpn
  setup_middle_server
  setup_bot
  start_docker
}

vpnsetup "$@"
