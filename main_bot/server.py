import re
import subprocess
import os
import shutil

import config
from config import set_key_env


def get_all_processes(server=None):
    try:
        result = subprocess.run(f'/usr/bin/tdbdump {config.tdb_file_ppp}', shell=True, capture_output=True, text=True)
        processes = []
        for line in result.stdout.split('\n'):
            if 'PEERNAME' in line:
                payload = re.search(r'"(.*)"', line).group(1)
                payload = payload.replace("\\00", "").replace("\x00", "")
                data = dict(item.split("=", 1) for item in payload.split(";") if "=" in item)
                processes.append(
                    (
                        data.get("PPPD_PID"),
                        data.get("IPREMOTE"),
                        data.get("PEERNAME")
                    )
                )
        return processes
    except Exception as e:
        return str(e)


def delete_session(server=None, username=None):
    try:
        # Выполнение команды ps с grep
        result = get_all_processes()
        # Поиск строк, содержащих xl2tpd и IP-адрес
        processes = [info for info in result if info[2] == username or username is None]
        for proc in processes:
            subprocess.run(f'/usr/bin/kill {proc[0]}', shell=True, capture_output=True, text=True)
        if not config.multi_connect:
            if username is None:
                subprocess.run(f'/usr/bin/rm -f /var/locks/*.lock', shell=True, capture_output=True, text=True)
            else:
                subprocess.run(f'/usr/bin/rm -f /var/locks/{username}.lock', shell=True, capture_output=True, text=True)
        return True
    except Exception:
        return False


def reboot_vpn():
    subprocess.run('/usr/bin/systemctl restart xl2tpd.service', shell=True, capture_output=True, text=True)


def write_users_to_file(users, server=None):
    try:
        # Открываем файл для записи
        with open(config.output_file, 'w') as file:
            # Записываем данные пользователей в файл
            for username, password in users:
                file.write(f'"{username}" l2tpd "{password}" *\n')
        return None
    except Exception as e:
        return e


def edit_multi_connect(enabled: bool):
    config.load_env()
    vpn_all: bool = True # Проверяем надо ли что-то менять в настройках сервера
    env = enabled == config.multi_connect

    vpn_config: bool = open(config.multi_connect_conf).read().strip() == "yes"

    if vpn_config != enabled:
        open(config.multi_connect_conf, "w").write('yes' if enabled else 'no')
        vpn_all = False

    if config.multi_connect != enabled:
        set_key_env(config.multi_connect_key, 'Y' if enabled else 'N')
        vpn_all = False

    if not os.path.exists('/var/locks'):
        os.mkdir("/var/locks")
        os.chmod('/var/locks', 0o777)

    if count_need_edit > 0:
        reboot_vpn()

    if vpn_all:
        if env:
            return 'Уже включен' if enabled else 'Уже выключен'
        elif not env:
            return 'Уже включен, просто был не изменен конфиг' if enabled else 'Уже выключен, просто был не изменен конфиг'
    return None


def reboot_server():
    subprocess.run('/usr/sbin/reboot', shell=True, capture_output=True, text=True)


def update_bot():
    subprocess.run('/usr/bin/git fetch && /usr/bin/git pull', shell=True, capture_output=True, text=True)
    restart_bot()

def restart_bot():
    subprocess.run('/usr/bin/systemctl restart vpn_bot.service', shell=True, capture_output=True, text=True)

def get_ipsec_key():
    with open(config.ipsec_file, 'r') as file:
        text = file.read()
    matches = re.findall(r':\s*PSK\s+(?:"([^"]+)"|([^\s"\n]+))', text, flags=re.IGNORECASE)
    keys = [m[0] or m[1] for m in matches]
    for i, key in enumerate(keys, 1):
        return key
    return None


def get_current_users_vpn():
    with open(config.output_file, 'r') as file:
        lines = file.readlines()
        users = []
        for passw in lines:
            info = passw.split()
            if info[1] == "l2tpd":
                users.append((info[0].strip('"'), info[2].strip('"')))
        return users