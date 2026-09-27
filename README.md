Установка на сервере Debian

Чистая установка на сервер

    apt install curl -y
    mkdir -p /app && cd /app
    curl https://raw.githubusercontent.com/Ferrostol/tg_bot_vpn_l2/refs/heads/final/install.sh >> install.sh
    chmod +x install.sh
    ./install.sh

Установка на сервер в docker
    
    mkdir -p /app && cd /app
    apt install curl -y
    curl https://raw.githubusercontent.com/Ferrostol/tg_bot_vpn_l2/refs/heads/final/docker/install.sh >> install.sh
    chmod +x install.sh
    ./install.sh

После этого пишем боту /start и регистрируемся первыми в качестве администратора
