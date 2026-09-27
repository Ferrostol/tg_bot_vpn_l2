import os

from dotenv import load_dotenv, set_key


# Пути до файлов
database_file = 'others/users.db'              # БД
tdb_file_ppp = 'others/ppp_connect.tdb'     # Файл с информацией о текущих подключениях к vpn
output_file = 'others/login_password_vpn'   # Файл с текущими пользователями vpn
ipsec_file = 'others/ipsec_key.secrets'       # Файл с секретным ключем
multi_connect_conf = 'others/multi_connect.conf'          # Файл с конфигурацией работы vpn в мультиконнект режиме

token = None
vpn_request = None
multi_connect = None
multi_connect_key = 'MULTI_CONNECT'


def load_env():
    global multi_connect, token, vpn_request
    load_dotenv(override=True)
    multi_connect = True if os.getenv(multi_connect_key) in ('Yy') else False
    vpn_request = True if os.getenv('USE_VPN') in ('Yy') else False
    token = os.getenv('TOKEN')

def set_key_env(key, value):
    set_key(".env", key, value, quote_mode='auto')
    load_env()

load_env()