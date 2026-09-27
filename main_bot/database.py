import sqlite3

from config import database_file


# Декоратор для работы с базой данных
def job_database(func):
    def wrapper(*args, **kwargs):
        result = None
        conn = None
        try:
            conn = sqlite3.connect(database_file)
            c = conn.cursor()
            result = func(c, *args, **kwargs)
            if result == 'edit':
                conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при работе с базой данных SQLite: {e}")
        finally:
            if conn:
                conn.close()
        return result
    return wrapper



# Создаем таблицы для проекта
@job_database
def create_all_tables(cursor):
    cursor.execute('''CREATE TABLE IF NOT EXISTS servers
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      domain TEXT NULL,
                      ip TEXT NULL,
                      main BOOLEAN default false
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    status INTEGER NOT NULL default 1,
                    server INTEGER REFERENCES servers NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tg_users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    enabled integer default 0,
                    role TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tg_ls_usr_vpn
                    (tg_usr INTEGER REFERECES tg_users,
                    usr INTEGER REFERECES users)''')
    return 'edit'



# Работа с пользователями из таблицы users
@job_database
def add_user(cursor, username, password, server):
    cursor.execute("INSERT INTO users (username, password, server) VALUES (?, ?, ?)", (username, password, server))
    return 'edit'

@job_database
def delete_vpn_user(cursor, username, server):
    cursor.execute("delete from users where username = ?", (username, ))
    return 'edit'

@job_database
def get_count_users(cursor):
    cursor.execute("SELECT count(1) FROM users")
    users = cursor.fetchone()
    return users[0]


@job_database
def enable_user_vpn(cursor, username, enabled, server):
    cursor.execute("update users set status = ? WHERE username=?", (enabled, username))
    return 'edit'

@job_database
def get_all_username_vpn(cursor, server = None, enabled=None):
    cursor.execute("SELECT username, password, status, server FROM users where coalesce(?, status) = status and coalesce(?, server) = server"
                   , (enabled, server))
    users = cursor.fetchall()
    if not server is None:
        users = [usr[:-1] for usr in users]
    return users



# Работа с пользователями TG из таблицы tg_users
@job_database
def add_tg_user(cursor, telegram_user_id, username, role, enabled):
    if username is None:
        username = 'Нет имени пользователя'
    cursor.execute("INSERT INTO tg_users (telegram_user_id, username, role, enabled) VALUES (?, ?, ?, ?)",
                   (telegram_user_id, username, role, enabled))
    return 'edit'

@job_database
def delete_tg_user(cursor, telegram_user_id):
    cursor.execute("delete from tg_users where telegram_user_id = ?", (telegram_user_id, ))
    return 'edit'

@job_database
def get_all_tg_username(cursor, username=None, enabled=None):
    cursor.execute(
        '''SELECT telegram_user_id, username, role, enabled
        FROM tg_users where (enabled = ? or ? is null) and (username = ? or ? is null)''',
        (enabled, enabled, username, username))
    users = cursor.fetchall()
    return users

@job_database
def get_count_users(cursor):
    cursor.execute("SELECT count(1) FROM tg_users")
    users = cursor.fetchone()
    return users[0]

@job_database
def get_enable_user(cursor, user_id_chat):
    cursor.execute("SELECT enabled FROM tg_users WHERE telegram_user_id=?", (user_id_chat,))
    result = cursor.fetchone()
    return result[0] if result else None

@job_database
def get_role_user(cursor, user_id_chat):
    cursor.execute("SELECT role FROM tg_users WHERE telegram_user_id=?", (user_id_chat,))
    result = cursor.fetchone()
    return result[0] if result else None

@job_database
def enable_user_tg(cursor, username, enabled):
    cursor.execute("update tg_users set enabled = ? WHERE username=?", (enabled, username))
    return 'edit'




# Работа с таблицей связи пользователя TG с его аккаунтами tg_ls_usr_vpn

@job_database
def get_my_account(cursor, user_id):
    cursor.execute(
        '''select u.username, u.password
        from tg_users tu, tg_ls_usr_vpn tluv, users u
        where tu.id = tluv.tg_usr and tluv.usr = u.id and tu.telegram_user_id = ?''',
        (user_id,))
    users = cursor.fetchall()
    return users

@job_database
def connect_tg_vpn(cursor, usr_id, vpn_name):
    cursor.execute(
        '''insert into tg_ls_usr_vpn (tg_usr, usr)
        values ((select id from tg_users where telegram_user_id = ?), (select id from users where username = ?))''',
        (usr_id, vpn_name))
    return 'edit'

@job_database
def unconnect_user(cursor, usr_id, vpn_name):
    cursor.execute(
        '''delete from tg_ls_usr_vpn
        where   tg_usr = (select id from tg_users where telegram_user_id = ?)
                and usr = (select id from users where username = ?)''',
        (usr_id, vpn_name))
    return 'edit'



# Информация по серверам из таблицы servers
@job_database
def add_server(cursor, name, domain, ip, main = False):
    cursor.execute("INSERT INTO servers (name, domain, ip, main) VALUES (?, ?, ?, ?)", (name, domain, ip, main))
    return 'edit'

@job_database
def delete_server(cursor, id_server):
    cursor.execute("delete from servers where id = ?", (id_server, ))
    return 'edit'

@job_database
def get_count_servers(cursor):
    cursor.execute("SELECT count(1) FROM servers")
    users = cursor.fetchone()
    return users[0]


@job_database
def get_all_servers(cursor, enabled=None):
    cursor.execute("SELECT id, name, domain, ip, main FROM servers")
    users = cursor.fetchall()
    return users