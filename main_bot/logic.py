from telebot import TeleBot, types, apihelper

import database
import server
import config
from buttons import Button, Result, start_buttons


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
                database.add_user(passw[0], passw[1], curr_server)




def check_enable_user(user_id, username):
    enabled = database.get_enable_user(user_id)
    if enabled is None:
        database.add_tg_user(user_id, username, 'user', 0)
        return False
    elif enabled == 1:
        return True
    return False


def check_tg_usr(bot: TeleBot, message: types.Message):
    if not database.get_count_users():
        database.add_tg_user(message.chat.id, message.from_user.username, 'admin', 1)
        bot.send_message(message.chat.id, "Пользователей нет в системе, вы добавлены в качестве администратора в систему",
                         reply_markup=start_buttons.get_markup(role=database.get_role_user(message.chat.id)))
        return False
    if not check_enable_user(message.chat.id, message.from_user.username):
        bot.send_message(message.chat.id,
                         "Вам запрещен доступ к возможностям бота, напишите администратору для разблокировки")
        return False
    return True


def next_step(message: types.Message, bot: TeleBot, type_in: str, next=None, *args):
    if message.from_user.is_bot:
        bot.send_message(message.chat.id, "Доступ запрещен")
        return
    if not check_tg_usr(bot, message):
        return
    role = database.get_role_user(message.chat.id)
    result = next(message.text, role, message, *args)
    if result.btn.parse_mode == "markdown":
        md_content = types.InputRichMessage(markdown=result.text)
        msg = bot.send_rich_message(
            message.chat.id,
            rich_message=md_content,
            reply_markup=result.btn.get_markup(role=role)
        )
    else:
        msg = bot.send_message(
            message.chat.id,
            result.text,
            reply_markup=result.btn.get_markup(role=role),
            parse_mode=result.btn.parse_mode
        )
    if result.next_step is not None:
        bot.register_next_step_handler(msg, next_step, bot, None, result.next_step)


def check_button_call(bot: TeleBot, call, role: str):
    chat_id = call.message.chat.id
    bot.clear_step_handler(call.message)
    btn = Button.get_buttons(start_buttons, role, call.data, chat_id)
    while True:
        result: Result = btn.analize(btn, chat_id)
        if result is not None:
            btn = result.btn
            text = result.text
            next = result.next_step
        elif btn.is_work:
            result: Result = btn.work_def(btn, chat_id, role, bot)
            btn: Button = result.btn
            text = result.text
            next = result.next_step
        else:
            text = btn.text
            next = None
        if btn.get_first_if_one:
            keys = btn.get_keys(chat_id)
            if len(keys) <= (2 if btn.can_back else 1):
                btn = keys[0]
                continue
        break
    try:
        if btn.parse_mode == "markdown":
            md_content = types.InputRichMessage(markdown=result.text)
            bot.edit_message_text(
                rich_message=md_content,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=btn.get_markup(role=role, chat_id=chat_id)
            )
        else:
            bot.edit_message_text(
                text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=btn.get_markup(role=role, chat_id=chat_id),
                parse_mode=btn.parse_mode
            )
        if next is not None:
            bot.register_next_step_handler(call.message, next_step, bot, None, next)
    except apihelper.ApiTelegramException as e:
        if "message is not modified" in e.description:
            pass
        else:
            print(e)
    except Exception as e:
        print(e)


def send_file(bot: TeleBot, chat_id, file_path):
    with open(file_path, 'rb') as f:
        bot.send_document(chat_id, f)

def get_file_and_save(bot: TeleBot, message, file_path):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(file_path, 'wb') as f:
        f.write(downloaded_file)