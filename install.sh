#!/bin/bash

set -euo pipefail

CURRENT_DIR="$(pwd)"

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

show_menu() {
  clear
  echo "===== SETUP MENU ====="

  for i in "${!TASK_LABELS[@]}"; do
    status="[ ]"

    if [[ ${TASK_ENABLED[$i]} -eq 1 ]]; then
      status="[x]"
    fi

    printf "%d) %s %s\n" \
      "$((i + 1))" \
      "$status" \
      "${TASK_LABELS[$i]}"
  done

  echo
  echo "0) FINISH"
  echo
  echo "Введите номер пункта для включения/выключения."
}

toggle_task() {
  local index=$1

  if [[ ${TASK_ENABLED[$index]} -eq 1 ]]; then
    TASK_ENABLED[$index]=0
  else
    TASK_ENABLED[$index]=1
  fi
}

vpnsetup() {
  while true; do
    show_menu

    read -rp "Выбор: " choice

    # FINISH
    if [[ "$choice" == "0" ]]; then
      break
    fi

    # Проверка числа
    if [[ "$choice" =~ ^[0-9]+$ ]]; then
      index=$((choice - 1))

      if (( index >= 0 && index < ${#TASK_LABELS[@]} )); then
        toggle_task "$index"
      fi
    fi
  done
  setup
}

# Основные функции
update_kernel() {
  if [[ "${UPDATE_KERNEL}" -eq 1 ]]; then
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
  if [[ "${INSTALL_ZSH}" -eq 1 ]]; then
    apt update && apt upgrade -y
    apt install net-tools git wget zsh htop -y
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
  fi
}

clone_git() {
  if [[ "${CLONE_GIT}" -eq 1 ]]; then
    cd "$CURRENT_DIR"
    git clone https://github.com/Ferrostol/tg_bot_vpn_l2.git
    cd tg_bot_vpn_l2
    git switch final
    cd "$CURRENT_DIR"
  fi
}

configure_vars() {
  if [[ "${INSTALL_VPN}" -eq 1 ]]; then
    prompt_until_nonempty USERNAME_LOGIN "Введите имя пользователя VPN (USERNAME_LOGIN)" "login"
    prompt_until_nonempty USERNAME_PASSWORD "Введите пароль VPN (USERNAME_PASSWORD)" "password"
    prompt_until_nonempty PSK_KEY "Введите PSK_KEY (Pre-Shared Key)(PSK_KEY)" "psk"
    if [[ "${MIDDLE_VPN}" -eq 1 ]]; then
      prompt_until_nonempty VPN_L2TP_NET "Укажите подсеть (VPN_L2TP_NET)" "10.1.0.0/16"
      prompt_until_nonempty VPN_L2TP_LOCAL "Укажите gateway (VPN_L2TP_LOCAL)" "10.1.0.1"
      prompt_until_nonempty VPN_L2TP_POOL "Укажите пул адресов (VPN_L2TP_POOL)" "10.1.0.10-10.1.254.254"
      prompt_until_nonempty VPN_IP "Введите IP конечного VPN (VPN_IP)" "localhost"
      prompt_until_nonempty VPN_USER "Введите имя пользователя конечного VPN (VPN_USER)" "login"
      prompt_until_nonempty VPN_PASSWORD "Введите пароль конечного VPN (VPN_PASSWORD)" "password"
    else
      prompt_until_nonempty VPN_L2TP_NET "Укажите подсеть (VPN_L2TP_NET)" "192.168.42.0/16"
      prompt_until_nonempty VPN_L2TP_LOCAL "Укажите gateway (VPN_L2TP_LOCAL)" "192.168.42.1"
      prompt_until_nonempty VPN_L2TP_POOL "Укажите пул адресов (VPN_L2TP_POOL)" "192.168.42.10-192.168.42.250"
    fi

    prompt_until_nonempty_yn MULTI_CONNECT "Разрешить одновременные подключения" "Y"
    if [[ "${EXISTS_DOMAIN}" -eq 1 ]]; then
      prompt_until_nonempty DOMAIN "Введите домен для текущего сервера" ""
    fi
  fi
  if [[ "${INSTALL_BOT}" -eq 1 ]]; then
    prompt_until_nonempty BOT_TOKEN "Введите Telegram bot token (BOT_TOKEN)" "NONE"
    prompt_until_nonempty USE_VPN "Использовать vpn для бота" "Y"
  fi
}

install_pkg() {
  if [[ "${SETUP_PKG}" -eq 1 ]]; then
    apt update
    apt install -y git wget tdb-tools
    if [[ "${INSTALL_PYTHON}" -eq 1 ]]; then
      apt-get install -y \
        zlib1g-dev libbz2-dev libreadline-dev llvm libncurses5-dev libncursesw5-dev \
        xz-utils tk-dev liblzma-dev python3-dev python3-lxml libxslt-dev libffi-dev \
        libssl-dev gnumeric libsqlite3-dev libpq-dev libxml2-dev libxslt1-dev \
        libjpeg-dev libfreetype6-dev libcurl4-openssl-dev
    fi
  fi
}

install_vpn() {
  if [[ "${INSTALL_VPN}" -eq 1 ]]; then
    cd "$CURRENT_DIR"
    wget https://get.vpnsetup.net -O vpn.sh
    chmod +x vpn.sh
    VPN_IPSEC_PSK="$PSK_KEY" \
    VPN_USER="$USERNAME_LOGIN" \
    VPN_PASSWORD="$USERNAME_PASSWORD" \
    VPN_L2TP_NET="$VPN_L2TP_NET" \
    VPN_L2TP_LOCAL="$VPN_L2TP_LOCAL" \
    VPN_L2TP_POOL="$VPN_L2TP_POOL" \
    VPN_DNS_NAME="$DOMAIN" \
    sh vpn.sh
  fi
}

setup_vpn() {
  if [[ "${INSTALL_VPN}" -eq 1 && "${SETUP_VPN}" -eq 1 ]]; then
    cd "$CURRENT_DIR"/tg_bot_vpn_l2/config

    if [[ "${MIDDLE_VPN}" -eq 1 ]]; then
      cd vpn_client
      cat client.conf > /etc/ipsec.d/client.conf
      sed -i "s|VPN_IP|$VPN_IP|g" /etc/ipsec.d/client.conf
      cat options.l2tpd.client >> /etc/ppp/options.l2tpd.client
      sed -i "s|VPN_USER|$VPN_USER|g" /etc/ppp/options.l2tpd.client
      sed -i "s|VPN_PASSWORD|$VPN_PASSWORD|g" /etc/ppp/options.l2tpd.client
      cat xl2tpd.conf >> /etc/xl2tpd/xl2tpd.conf
      sed -i "s|VPN_IP|$VPN_IP|g" /etc/xl2tpd/xl2tpd.conf
      cat connect_client.service > /etc/systemd/system/connect_client.service
    fi

    mkdir -p /var/locks
    chmod 777 /var/locks
    cat config/vpn_server/ip-up >> /etc/ppp/ip-up
    cat config/vpn_server/ip-down >> /etc/ppp/ip-down
    [[ "$MULTI_CONNECT" =~ ^[Yy]$ ]] && echo "yes" > /etc/ppp/multi_connect.conf
    [[ "$MULTI_CONNECT" =~ ^[Nn]$ ]] && echo "no"  > /etc/ppp/multi_connect.conf
  fi
}

fix_ikev2() {
  if [[ "${FIX_IKEV2}" -eq 1 ]]; then
    sed -i "s|Disconnect|Сonnect|g" /opt/src/ikev2.sh
    sed -i "s|Disconnect|Сonnect|g" /root/*.mobileconfig
  fi
}


install_sing_box() {
  if [[ "${INSTALL_SING_BOX}" -eq 1 ]]; then
    cd "$CURRENT_DIR"
    bash <(curl -fsSL https://sing-box.app/install.sh)

    cd tg_bot_vpn_l2/config/sing-box

    # Создаем папку для хранения конфигов
    mkdir -p "$CURRENT_DIR"/tg_bot_vpn_l2/others/sing-box
    # Скрипт для инициализации маршрута от L2TP до sing-box
    cp sing_init.sh "$CURRENT_DIR"/tg_bot_vpn_l2/others/sing-box/
    chmod +x "$CURRENT_DIR"/tg_bot_vpn_l2/others/sing-box/sing_init.sh
    sed -i "s|VPN_L2TP_NET|${VPN_L2TP_NET%%/*}|g" "$CURRENT_DIR"/tg_bot_vpn_l2/others/sing_init.sh

    # Создаем демона для инициализации маршрута от L2TP до sing-box
    cat sing_init.service > /etc/systemd/system/sing_init.service
    sed -i "s|/CURRENT_DIR/|$CURRENT_DIR/|g" /etc/systemd/system/sing_init.service

    # Скрипт для выбора конфига распределения трафика sing-box
    cp select_config.sh "$CURRENT_DIR"/tg_bot_vpn_l2/others/sing-box/
    chmod +x "$CURRENT_DIR"/tg_bot_vpn_l2/others/sing-box/select_config.sh
    sed -i "s|/CURRENT_DIR/|$CURRENT_DIR/|g" "$CURRENT_DIR"/tg_bot_vpn_l2/others/sing-box/select_config.sh

    # Создание демона для выбора конфига распределения трафика
    cat sing_config.service > /etc/systemd/system/sing_config.service
    sed -i "s|/CURRENT_DIR/|$CURRENT_DIR/|g" /etc/systemd/system/sing_config.service

    # Создание таймера демона для выбора конфига распределения трафика
    cat sing_config.timer > /etc/systemd/system/sing_config.timer
  fi
}

install_python() {
  if [[ "${INSTALL_PYTHON}" -eq 1 ]]; then
    cd "$CURRENT_DIR"
    mkdir -p tmp
    cd tmp
    wget https://www.python.org/ftp/python/3.12.2/Python-3.12.2.tgz
    tar xvf Python-3.12.2.tgz
    cd Python-3.12.2
    mkdir -p ~/.python
    ./configure --enable-optimizations --prefix=/root/.python
    make -j"$(nproc)"
    make altinstall

    /root/.python/bin/python3.12 -m pip install -U pip
    export PATH=/root/.python/bin:$PATH
    cd "$CURRENT_DIR"
  fi
}

install_bot() {
  if [[ "${INSTALL_BOT}" -eq 1 ]]; then
    cd "$CURRENT_DIR"/tg_bot_vpn_l2
    /root/.python/bin/python3.12 -m venv venv
    . ./venv/bin/activate
    pip install -r ./main_bot/requirements.txt

    cp ./config/vpn_bot.service /etc/systemd/system
    sed -i "s|/CURRENT_DIR/|$CURRENT_DIR/|g" /etc/systemd/system/vpn_bot.service
    echo "TOKEN=$BOT_TOKEN" > .env
    echo "USE_VPN=$USE_VPN" >> .env
    [[ "$MULTI_CONNECT" =~ ^[Yy]$ ]] && echo "MULTI_CONNECT=Y" >> .env
    [[ "$MULTI_CONNECT" =~ ^[Nn]$ ]] && echo "MULTI_CONNECT=N"  >> .env

    mkdir -p "$CURRENT_DIR"/tg_bot_vpn_l2/others
    cd "$CURRENT_DIR"/tg_bot_vpn_l2/others
    # Создаем ссылки на файлы vpn для использования в боте
    ln -s '/var/run/pppd2.tdb' ppp_connect.dtb
    ln -s '/etc/ipsec.secrets' ipsec_key.secrets
    ln -s '/etc/ppp/chap-secrets' login_password_vpn
    ln -s '/etc/ppp/multi_connect.conf' multi_connect.conf
  fi
}

start_all() {
  systemctl daemon-reload
  if [[ "${INSTALL_VPN}" -eq 1 ]]; then
    systemctl restart ipsec.service
    systemctl restart xl2tpd.service
    if [[ "${MIDDLE_VPN}" -eq 1 ]]; then
      systemctl enable --now connect_client.service
    fi
  fi
  if [[ "${INSTALL_BOT}" -eq 1 ]]; then
    systemctl enable vpn_bot.service
    systemctl start vpn_bot.service
  fi

  if [[ "${INSTALL_SING_BOX}" -eq 1 ]]; then
    systemctl enable --now sing_init.service
    systemctl enable --now sing-box.service
    systemctl enable --now sing_config.timer
  fi
}

setup() {
  export UPDATE_KERNEL="${TASK_ENABLED[0]}"
  export INSTALL_ZSH="${TASK_ENABLED[1]}"
  export CLONE_GIT="${TASK_ENABLED[2]}"
  export SETUP_PKG="${TASK_ENABLED[3]}"
  export INSTALL_VPN="${TASK_ENABLED[4]}"
  export MIDDLE_VPN="${TASK_ENABLED[5]}"
  export SETUP_VPN="${TASK_ENABLED[6]}"
  export FIX_IKEV2="${TASK_ENABLED[7]}"
  export INSTALL_SING_BOX="${TASK_ENABLED[8]}"
  export INSTALL_PYTHON="${TASK_ENABLED[9]}"
  export INSTALL_BOT="${TASK_ENABLED[10]}"
  export EXISTS_DOMAIN="${TASK_ENABLED[11]}"
  update_kernel
  install_zsh
  configure_vars
  install_pkg
  clone_git
  install_vpn
  setup_vpn
  fix_ikev2
  install_sing_box
  install_python
  install_bot
  start_all
}


# Массив текста выдаваемый пользователю
TASK_LABELS=(
  "Изменение ядра"
  "Установка zsh"
  "Клонировать репозиторий"
  "Установка пакетов"
  "Установка VPN"
  "Промежуточный VPN"
  "Настройка конфигов VPN"
  "Исправление OnDemandRules для IKEv2"
  "Установка sing-box"
  "Установка python"
  "Установка бота"
  "Наличие домена для текущего сервера"
)

# Состояние пунктов (0 = OFF, 1 = ON)
TASK_ENABLED=(0 0 1 1 1 1 1 1 1 1 1 1)

if [[ "$(uname -r)" == *cloud* ]]; then
    TASK_ENABLED=(1 0 0 0 0 0 0 0 0 0 0 0)
elif [[ ! "$SHELL" == *zsh* ]]; then
    TASK_ENABLED=(0 1 0 0 0 0 0 0 0 0 0 0)
fi



## Defer setup until we have the complete script
vpnsetup "$@"