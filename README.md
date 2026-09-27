Установка на сервере Debian

Чистая установка на сервер

    apt install curl -y
    mkdir -p /app && cd /app
    curl https://raw.githubusercontent.com/Ferrostol/tg_bot_vpn_l2/refs/heads/final/install.sh > install.sh
    chmod +x install.sh
    ./install.sh

Установка на сервер в docker(часть функций бота не работают в docker режиме)
    
    mkdir -p /app && cd /app
    apt install curl -y
    curl https://raw.githubusercontent.com/Ferrostol/tg_bot_vpn_l2/refs/heads/final/install_docker.sh > install.sh
    chmod +x install.sh
    ./install.sh

После этого пишем боту /start и регистрируемся первыми в качестве администратора


Удаление на сервере в docker

    curl https://raw.githubusercontent.com/Ferrostol/tg_bot_vpn_l2/refs/heads/final/docker/uninstall.sh > uninstall.sh
    chmod +x uninstall.sh
    ./uninstall.sh


TODO лист:

| Что сделать                                             | Проблема сейчас                                                                          |
|---------------------------------------------------------|------------------------------------------------------------------------------------------|
| Реализовать корректное удаление сессий пользователя     | При удалении сессии пользователя через kill информация не удаляется из файла tdb         |
| Исправить кнопки, которые некорректно работают в docker | Не работает обновление бота, при переписывании удалены кнопки перезагрузки vpn и сервера |

