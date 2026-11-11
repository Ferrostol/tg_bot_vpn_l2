# Библиотека для телеграм бота
from telebot import TeleBot, types
import telebot.apihelper

# Библиотеки для работы бота через впн
import socket
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

# Модули бота
import config
from logic import start_program, check_enable_user
from buttons import start_buttons
import database

# Подключаем самописную библиотеку для кнопок
from butnlib.botLogic import LogicBot


if config.vpn_request:
    class Tun0Adapter(HTTPAdapter):
        def init_poolmanager(self, *args, **kwargs):
            kwargs["socket_options"] = [
                (socket.SOL_SOCKET, socket.SO_BINDTODEVICE, b"vpn")
            ]
            self.poolmanager = PoolManager(*args, **kwargs)

    session = requests.Session()
    session.mount("https://", Tun0Adapter())
    session.mount("http://", Tun0Adapter())
    telebot.apihelper.session = session

bot = TeleBot(config.token)
logic_bot = LogicBot(start_buttons, bot)
start_program()


def check_tg_usr(message: types.Message):
    if not database.get_count_users():
        database.add_tg_user(message.chat.id, message.from_user.username, 'admin', 1)
        bot.send_message(message.chat.id,
                         "Пользователей нет в системе, вы добавлены в качестве администратора в систему",
                         reply_markup=logic_bot.get_markup(start_buttons, chat_id=message.chat.id))
        return False
    if not check_enable_user(message.chat.id, message.from_user.username):
        bot.send_message(message.chat.id,
                         "Вам запрещен доступ к возможностям бота, напишите администратору для разблокировки")
        return False
    return True


@bot.message_handler(commands=['start'])
def start_message(message: types.Message):
    if message.from_user.is_bot:
        bot.send_message(message.chat.id, "Доступ запрещен")
        return
    if not check_tg_usr(message):
        return

    bot.send_message(message.chat.id,
                     'Доступные команды',
                     reply_markup=logic_bot.get_markup(start_buttons, chat_id=message.chat.id))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.from_user.is_bot:
        bot.send_message(message.chat.id, "Доступ запрещен")
        return
    if not check_tg_usr(call.message):
        return
    logic_bot.check_button_click(call)
    bot.answer_callback_query(call.id)

bot.infinity_polling(skip_pending=True)
