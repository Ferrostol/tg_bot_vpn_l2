from telebot import TeleBot, types
import telebot.apihelper

import socket
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

import config
from logic import start_program, check_tg_usr, check_button_call
from database import get_role_user
from buttons import start_buttons

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
start_program()


@bot.message_handler(commands=['start'])
def start_message(message: types.Message):
    if message.from_user.is_bot:
        bot.send_message(message.chat.id, "Доступ запрещен")
        return
    if not check_tg_usr(bot, message):
        return

    bot.send_message(message.chat.id,
                     'Доступные команды',
                     reply_markup=start_buttons.get_markup(role=get_role_user(message.chat.id)))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.from_user.is_bot:
        bot.send_message(message.chat.id, "Доступ запрещен")
        return
    if not check_tg_usr(bot, call.message):
        return
    check_button_call(bot,call, get_role_user(call.from_user.id))
    bot.answer_callback_query(call.id)

bot.infinity_polling()
