from telebot import TeleBot, types, apihelper

import database
import server


def start_program():
    database.create_all_tables()
    # Добавление текущего сервера в список серверов
    if database.get_count_servers() == 0:
        database.add_server('main', 'localhost', None, True)
        database.add_server('vpn', 'others', None, False)
    curr_server = [el[0] for el in database.get_all_servers() if el[4]][-1]

    # Проверка добавления текущих vpn пользователей
    if database.get_count_users() == 0:
        password = server.get_current_users_vpn()
        if len(password) > 0:
            for passw in password:
                database.add_user(passw[0], passw[1], curr_server, passw[2])


def check_enable_user(user_id, username):
    enabled = database.get_enable_user(user_id)
    if enabled is None:
        database.add_tg_user(user_id, username, 'user', 0)
        return False
    elif enabled == 1:
        return True
    return False


def send_file(bot: TeleBot, chat_id, file_path):
    with open(file_path, 'rb') as f:
        bot.send_document(chat_id, f)

def get_file_and_save(bot: TeleBot, message, file_path):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(file_path, 'wb') as f:
        f.write(downloaded_file)