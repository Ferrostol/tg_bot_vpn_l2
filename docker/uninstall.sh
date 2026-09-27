#!/bin/bash
set -euo pipefail
PATH_FILE="/etc/my_vpn_server"


uninstall() {
  echo "Начинаю удаление"
  if [[ -f "$PATH_FILE" ]]; then
    CURR_DIR=$(cat $PATH_FILE)
    echo "Программа была установлена в $CURR_DIR"
    cd "$CURR_DIR"
    echo "Удаляем контейнер VPN"
    docker kill ipsec_server_container 2> /dev/null || true
    docker container rm ipsec_server_container 2> /dev/null || true
    docker image rm others-vpn 2> /dev/null || true
    echo "Контейнер VPN удален"

    echo "Удаляем контейнер sing-box"
    docker kill sing_box_container 2> /dev/null || true
    docker container rm sing_box_container 2> /dev/null || true
    echo "Контейнер sing-box удален"

    echo "Удаляем контейнер бота"
    docker kill my_bot_container 2> /dev/null || true
    docker container rm my_bot_container 2> /dev/null || true
    docker image rm others-bot 2> /dev/null || true
    echo "Контейнер бота удален"

    echo "Удаляем папки программы"
    rm -rf bot tg_bot_vpn_l2 vpn sing-box 2> /dev/null
    echo "Папки программы удалены"
    rm "$PATH_FILE"
  fi
  echo "Удаление завершено"
}

uninstall "$@"