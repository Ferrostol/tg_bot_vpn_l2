from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from prettytable import PrettyTable, TableStyle

from database import *
from server import *
import config
import logic

razdelitel = '__'


class Button:
    def __init__(
            self,
            key: str,                       # Ключ, по которому можно идентифицировать кнопку
            caption: str,                   # Отображаемое пользователю название кнопки
            text: str = None,               # Отображаемый пользователю текст вместе с кнопками
            buttons: list["Button"] = None, # Кнопки, которые находятся после нажатия данной кнопки
            is_admin: bool = False,         # Кнопка только для администратора
            can_back: bool = None,          # Необходимость добавления кнопки "Назад", в список кнопок
            parse_mode: str = None,         # Действие кнопки выводит определенный тип содержимого
            is_custom_keys: bool = False,   # Использовать вместо заранее заготовленных кнопок список кнопок полученных через функцию
            custom_keys_def = None,         # lambda функция по генерации списка кнопок, которые находятся после нажатия данной кнопки
            analize = None,                 # lambda функция условия для захода в кнопку
            is_work: bool = False,          # Нажатие кнопки выполняет действие
            work_def = None,                # lambda функция действия при нажатии кнопки
            visible: bool = True,
            get_first_if_one: bool = False  # Сразу переходить внутрь кнопки, если внутри текущей всего одна кнопка
    ):
        if text is None:
            text = caption
        if buttons is None:
            buttons = []

        self.key = key
        self.caption = caption
        self.text = text
        self.buttons = buttons
        self.is_admin = is_admin
        self.is_back = key.endswith(f'{razdelitel}back')
        self.parse_mode = parse_mode
        self.is_custom_keys = is_custom_keys
        self.custom_keys_def = custom_keys_def
        self.can_back = can_back
        self.analize = analize if analize is not None else lambda x, *args: None
        self.is_work = is_work
        self.work_def = work_def
        self.prev_button: Button = None
        self.keys_search = key
        self.visible = visible
        self.get_first_if_one = get_first_if_one

        if (can_back if can_back is not None else False) and not self.is_custom_keys:
            self.buttons.append(Button(f'{razdelitel}back', 'Назад', "Назад"))

        for btn in self.buttons:
            btn.prev_button = self
            if self.is_admin:
                btn.is_admin = self.is_admin
        self.__update_children_button()


    def __update_children_button(self):
        for btn in self.buttons:
            btn.keys_search = f"{self.keys_search}{razdelitel}{btn.key}"
            if self.is_admin:
                btn.is_admin = self.is_admin
            btn.__update_children_button()


    def get_keys(self, *args):
        if self.is_custom_keys:
            btns = self.custom_keys_def(self.key, *args)
            if self.can_back:
                btns.append(Button(f'{razdelitel}back', 'Назад', "Назад"))
            for btn in btns:
                btn.prev_button = self
                btn.keys_search = f"{self.keys_search}{razdelitel}{btn.key}"
                btn.__update_children_button()
        else:
            btns = self.buttons
        return btns


    def get_markup(self, role: str = 'user', chat_id = None):
        row = []
        for el in self.get_keys(chat_id):
            if not el.check_secure_user(role) or not el.visible:
                continue
            row.append(InlineKeyboardButton(el.caption, callback_data=el.keys_search))
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(*row)
        return markup

    def get_prev_button(self, chat_id, up_up: bool = False):
        def check_btn(bt):
            keys = bt.prev_button.get_keys(chat_id)
            if len(keys) <= (2 if bt.can_back else 1):
                bt = bt.prev_button
                return check_btn(bt)
            return bt
        btn = self
        if btn.is_back:
            btn = btn.prev_button
        btn = check_btn(btn)
        if up_up and btn.prev_button is not None:
            btn = check_btn(btn.prev_button)
        if btn.prev_button is not None:
            btn = btn.prev_button
        return btn

    def check_secure_user(self, role):
        if self.is_admin and role != 'admin':
            return False
        return True

    @staticmethod
    def get_buttons(btns: "Button", role: str, search_key: str, chat_id, *args):
        def get_button(btn, role: str, search_key: str):
            if not btn.check_secure_user(role):
                return None
            if not search_key.startswith(btn.keys_search):
                return None
            if btn.keys_search == search_key:
                return btn
            for el in btn.get_keys(*args):
                sb = get_button(el, role, search_key)
                if not sb is None:
                    return sb
            return None

        btn = get_button(btns, role, search_key)
        if btn is None:
            btn = btns

        if btn.is_back:
            btn = btn.get_prev_button(chat_id)
        return btn


class Result:
    def __init__(self, btn: Button, text: str, next_step = None):
        self.btn = btn
        self.text = text
        self.next_step = next_step



# Для создания рекурсивных функций
def make_recursive_lambda(template):
    return (lambda f: lambda *args: template(f(f), *args))(
           lambda f: lambda *args: template(f(f), *args))


def get_table_str(head: list, data: list):
    table = PrettyTable()
    table.field_names = head  # Установка заголовков столбцов
    for row in data:
        table.add_row(row)
    table.set_style(TableStyle.MARKDOWN)
    return table.get_string()





start_buttons = Button('start', 'Начало', 'Выберите действие', can_back=False, buttons=[
    Button('admin_tg', 'Админ TG', 'Выберите действие', is_admin=True, can_back=True, buttons=[
        Button('unlock', 'Дать доступ пользователю TG', 'Выберите пользователя для разблокировки', can_back=True, is_custom_keys=True,
               custom_keys_def=lambda key, *args: [
                   Button(el[0], el[1], is_work=True, work_def=(lambda el0=el[0], el1=el[1]: (
                       lambda self_btn, chat_id, *arg: (
                           Result(self_btn.get_prev_button(chat_id, True),
                                  "Пользователь разблокирован"
                                  if enable_user_tg(el0, 1) == 'edit'
                                  else f"Ошибка при разблокировке пользователя {el1}")
                       )))())
                   for el in get_all_tg_username(enabled=0)
               ], analize=lambda x, *args: None if len(x.get_keys(*args)) > 1 else Result(x.prev_button, 'Пользователей нет')),

        Button('delete', 'Удалить пользователя TG', 'Выберите пользователя для удаления', can_back=True, is_custom_keys=True,
               custom_keys_def=lambda key, *args: [
                   Button(el[0], el[1], is_work=True, work_def=(lambda el0=el[0], el1=el[1]: (
                       lambda self_btn, chat_id, *arg: (
                           Result(self_btn.get_prev_button(chat_id, True),
                                  "Пользователь удален"
                                  if delete_tg_user(el0) == 'edit'
                                  else f"Ошибка при удалении пользователя {el1}")
                       )))())
                   for el in get_all_tg_username()
               ], analize=lambda x, *args: None if len(x.get_keys(*args)) > 1 else Result(x.prev_button, 'Пользователей нет')),

        Button('lock', 'Заблокировать пользователя TG', 'Выберите пользователя для блокировки', can_back=True, is_custom_keys=True,
               custom_keys_def=lambda key, *args: [
                   Button(el[0], el[1], is_work=True, work_def=(lambda el0=el[0], el1=el[1]: (
                       lambda self_btn, chat_id, *arg: (
                           Result(self_btn.get_prev_button(chat_id, True),
                                  "Пользователь заблокирован"
                                  if enable_user_tg(el0, 0) == 'edit'
                                  else f"Ошибка при блокировке пользователя {el1}")
                       )))())
                   for el in get_all_tg_username(enabled=1)
               ], analize=lambda x, *args: None if len(x.get_keys(*args)) > 1 else Result(x.prev_button, 'Пользователей нет')),

        Button('show_users', 'Посмотреть пользователей TG', can_back=True, parse_mode="markdown", is_work=True,
               work_def=lambda self, chat_id, *arg: (
                   Result(self.prev_button, "Список пользователей пуст")
                   if not len((data := get_all_tg_username()))
                   else Result(self, get_table_str(['USR_ID', 'NAME', 'ROLE', 'ENABLED'], data))
                )),


    ]),
    Button('admin_serv', 'Админ VPN серверов', 'Выберите сервер', is_admin=True, can_back=True, is_custom_keys=True, get_first_if_one=True,
           custom_keys_def= lambda *args: [
               Button(f'srv_{srv[0]}', srv[1], f'Сервер {srv[1]}', can_back=True, buttons=[
                   Button('add_user_vpn', 'Добавить пользователя VPN', can_back=True, is_work=True,
                          work_def=lambda self, chat_id, role, *arg, server_id=srv[0]: Result(
                              self, 'Введите имя нового пользователя', make_recursive_lambda(lambda self_func, login, login_role, *args: (
                                  Result(Button.get_buttons(start_buttons, login_role, self.keys_search),'Ошибка создания пользователя')
                                  if not self.check_secure_user(login_role)
                                  else Result(self, "Введите пароль для пользователя", make_recursive_lambda(lambda self_func_pass, password, password_role, *args_2: (
                                      Result(Button.get_buttons(start_buttons, password_role, self.keys_search), 'Ошибка создания пользователя')
                                      if not self.check_secure_user(password_role)
                                      else Result(self.prev_button, f'Пользователь создан\nЛогин:{login}\nПароль:{password}\nОбщий ключ:{get_ipsec_key()}')
                                      if (
                                          add_user(login, password, server_id),
                                          write_users_to_file([(el[0], el[1]) for el in get_all_username_vpn(server=server_id, enabled=1)], server=server_id),
                                          len([el for el in get_all_username_vpn(server=server_id) if el[0] == login])
                                      )[-1] > 0
                                      else Result(self.prev_button, "Пользователь не создан")
                                  )))
                                  if len([el for el in get_all_username_vpn(server=server_id) if el[0] == login]) == 0
                                  else Result(self, "Такой пользователь уже существует. Введите имя нового пользователя", self_func)
                              ))
                          )),

                   Button('unlock_vpn', 'Разблокировать пользователя VPN', 'Выберите пользователя для разблокировки', can_back=True, is_custom_keys=True,
                          custom_keys_def=lambda key, *args, server_id=srv[0]: [
                                  Button(el[0], el[0], is_work=True, work_def=(lambda el0=el[0], el1=el[1], server_id=srv[0]: (
                                  lambda self_btn, chat_id, *arg: (
                                      Result(self_btn.get_prev_button(chat_id, True),
                                             f"Ошибка при разблокировки пользователя {el1}"
                                             if not enable_user_vpn(el0, 1, server_id) == 'edit'
                                             else "Пользователь разблокирован"
                                             if (err := write_users_to_file([(els[0], els[1]) for els in get_all_username_vpn(server=server_id, enabled=1)], server=server_id)) is None
                                             else f"Ошибка при разблокировки пользователя {el1}. Ошибка {err}")
                                  )))())
                              for el in get_all_username_vpn(server=server_id, enabled=0)
                          ], analize=lambda x, *args: None if len(x.get_keys(*args)) > 1 else Result(x.prev_button, 'Пользователей нет')),

                   Button('lock_vpn', 'Заблокировать пользователя VPN', 'Выберите пользователя для блокировки', can_back=True, is_custom_keys=True,
                          custom_keys_def=lambda key, *args, server_id=srv[0]: [
                              Button(el[0], el[0], is_work=True, work_def=(lambda el0=el[0], el1=el[1], server_id=srv[0]: (
                                  lambda self_btn, chat_id, *arg: (
                                      Result(self_btn.get_prev_button(chat_id, True),
                                             f"Ошибка при блокировке пользователя {el1}"
                                             if not enable_user_vpn(el0, 0, server_id) == 'edit'
                                             else "Пользователь заблокирован"
                                             if (err := write_users_to_file([(els[0], els[1]) for els in get_all_username_vpn(enabled=1)], server=server_id)) is None
                                             else f"Ошибка при блокировке пользователя {el1}. Ошибка {err}")
                                  )))())
                              for el in get_all_username_vpn(server=server_id, enabled=1)
                          ], analize=lambda x, *args: None if len(x.get_keys(*args)) > 1 else Result(x.prev_button, 'Пользователей нет')),

                   Button('delete_vpn', 'Удалить пользователя VPN', 'Выберите пользователя для удаления', can_back=True, is_custom_keys=True,
                          custom_keys_def=lambda key, *args, server_id=srv[0]: [
                              Button(el[0], el[0], is_work=True, work_def=(lambda el0=el[0], server_id=srv[0]: (
                                  lambda self_btn, chat_id, *arg: (
                                      Result(self_btn.get_prev_button(chat_id, True),
                                             f"Ошибка при удалении пользователя {el0}"
                                             if not delete_vpn_user(el0, server_id) == 'edit'
                                             else "Пользователь удален"
                                             if (err := write_users_to_file([(els[0], els[1]) for els in get_all_username_vpn(enabled=1)], server=server_id)) is None
                                             else f"Пользователь удален. Ошибка при обновлении файла с доступами. Ошибка {err}")
                                  )))())
                              for el in get_all_username_vpn(server=server_id)
                          ], analize=lambda x, *args: None if len(x.get_keys(*args)) > 1 else Result(x.prev_button, 'Пользователей нет')),

                   Button('del_all_ses', 'Удалить все сессии', is_work=True,
                          work_def=lambda self, *arg, server_id=srv[0]: Result(
                              self.prev_button,
                              'Все сессии удалены' if delete_session(server=server_id) else 'Ошибка удаления сессий'
                          )),
                   Button('show_all_ses', 'Посмотреть текущие сессии', can_back=True, parse_mode="markdown", is_work=True,
                          work_def=lambda self, chat_id, *arg, server_id=srv[0]: (
                              Result(self.prev_button, "Список сессий пуст")
                              if not len((data := get_all_processes(server=server_id)))
                              else Result(self, get_table_str(['PID', 'Local IP', 'Name'], data))
                          ), buttons=[
                           Button('reload', 'Обновить', can_back=True, parse_mode="markdown", is_work=True,
                                  work_def=lambda self, *arg: self.prev_button.work_def(self.prev_button, *arg))
                       ]),
                   Button('vpn_users', 'Посмотреть пользователей VPN', can_back=True, parse_mode="markdown", is_work=True,
                          work_def=lambda self, chat_id, *arg, server_id=srv[0]: (
                              Result(self.prev_button, "Список пользователей пуст")
                              if not len((data := get_all_username_vpn(server=server_id)))
                              else Result(self, get_table_str(['USR', 'PASSWORD', 'STATUS'], data))
                          ))
               ]) for srv in get_all_servers()
           ], analize=lambda x, chat_id, *args: None if get_count_servers() > 1 else Result(x.get_prev_button(chat_id), 'Отсутствуют сервера VPN')),

    Button('settings', 'Настройки', 'Выберите действие', is_admin=True, can_back=True, buttons= [
        Button('multi_connect', '1 user != 1 session', 'Изменение', can_back=True, is_custom_keys=True, custom_keys_def= lambda *args : [
            Button('enable', 'Выключить' if config.multi_connect else 'Включить', 'Подтвердите', can_back=True, buttons=[
                Button(name, 'Подтвердаю', is_work=True, visible=visible,
                       work_def=(lambda enabled_=config.multi_connect: (
                           lambda self_btn, chat_id, *args: (
                               Result(
                                   self_btn.get_prev_button(chat_id, True).get_prev_button(chat_id),
                                   'Настройка изменена'
                                   if (err := edit_multi_connect(not enabled_)) is None
                                   else err
                               )
                           )))())
                for name, visible in zip(['on', 'off'], [not config.multi_connect, config.multi_connect])
            ])
        ]),
        Button('reboot_vpn', 'Перезагрузить VPN', 'Перезагрузить?', can_back=True, buttons=[
            Button('confirm', '100% Да', is_work=True, work_def= lambda self_btn, chat_id, *args: (
                (reboot_vpn(), Result(self_btn.get_prev_button(chat_id, True), 'Перезагружено'))[-1]
            ))
        ]),
        Button('reboot_server', 'Перезагрузить сервер', can_back=True, buttons=[
            Button('confirm', '100% Да', is_work=True, work_def= lambda self_btn, *args: reboot_server())
        ]),
        Button('update_bot', 'Обновить бота', can_back=True, buttons=[
            Button('confirm', '100% Да', is_work=True, work_def= lambda self_btn, *args: update_bot())
        ]),
        Button('export_db', 'Экспорт БД', can_back=True, buttons=[
            Button('confirm', '100% Да', is_work=True,
                   work_def= lambda self_btn, chat_id, role, bot, *args: (
                       Result(self_btn.get_prev_button(chat_id, True),
                              (logic.send_file(bot, chat_id, config.database_file), 'Файл экспортирован')[-1])
                   ))
        ]),
        Button('import_bd','Импорт БД', can_back=True, buttons=[
            Button('confirm', '100% Да', is_work=True, can_back=True, work_def= lambda self_btn, chat_id, role, bot, *args: (
                Result(self_btn, 'Пришлите файл БД', make_recursive_lambda(lambda self_func, _, __, message, *args_1: (
                    Result(self_btn, 'Некорректный файл', self_func)
                    if not message.document
                    else (logic.get_file_and_save(bot, message, f"{config.database_file}"), write_users_to_file([(els[0], els[1]) for els in get_all_username_vpn(enabled=1)]), restart_bot())
                ))))
            )
        ]),
        Button('update_file_users','Обновить пользователей VPN', can_back=True, buttons=[
            Button('confirm', '100% Да', is_work=True, can_back=True, work_def= lambda self_btn, *args: (
                Result(self_btn, "Файл с пользователям обновлен"
                                  if (err := write_users_to_file([(els[0], els[1]) for els in get_all_username_vpn(enabled=1)])) is None
                                  else f"Ошибка при обновлении файла с доступами. Ошибка {err}")
            ))
        ])
    ]),

    Button('show_my_acc', 'Посмотреть свои аккаунты', can_back=True, parse_mode="markdown", is_work=True,
           work_def=lambda self, chat_id, *arg: (
               Result(self.prev_button, "Список пользователей пуст")
               if not len((data := get_my_account(chat_id)))
               else Result(self, get_table_str(['USR', 'PASSWORD'], data))
           )),

    Button('connect_acc', 'Привязать аккаунт', can_back=True, is_work=True,
           work_def=lambda self, chat_id, *arg: Result(
               self, 'Введите имя нового пользователя', make_recursive_lambda(lambda self_func, login, *args: (
                   Result(self, "Введите пароль для пользователя", make_recursive_lambda(lambda self_func_pass, password, *args_2: (
                       Result(self.prev_button, 'Аккаунт привязан к вам' if connect_tg_vpn(chat_id, login) == 'edit' else 'Ошибка привязки аккаунта')
                       if len([el for el in get_all_username_vpn() if el[0] == login and el[1] == password]) > 0
                       else Result(self, "Неверные данные входа, начните заново", self_func)
                   )))
                   if len([el for el in get_my_account(chat_id) if el[0] == login]) == 0
                   else Result(self, "Данный аккаунт уже привязан к вам", self_func)
               ))
           )),

    Button('unconnect_acc', 'Отвязать аккаунт', 'Выберете аккаунт для отвязки', can_back=True, is_custom_keys=True,
           custom_keys_def=lambda key, chat_id, *args: [
               Button(el[0], el[0], is_work=True,
                      work_def=(lambda el0=el[0]: (
                          lambda self_btn, *arg: Result(self_btn.prev_button.prev_button,
                                                        f'Аккаунт отвязан'
                                                        if unconnect_user(chat_id, el0) == 'edit'
                                                        else f'Ошибка отвязки аккаунта')
                      ))())
               for el in get_my_account(chat_id)
           ], analize=lambda x, chat_id, *args: None if len(x.get_keys(chat_id)) > 1 else Result(x.prev_button, 'У вас нет аккаунтов')),

    Button('del_my_ses', 'Удалить свои сессии', 'Выберете аккаунт для которого необходимо сбросить сессии', can_back=True, is_custom_keys=True,
           custom_keys_def=lambda key, chat_id, *args: [
               Button(el[0], el[0], is_work=True,
                      work_def=(lambda el0=el[0]: (
                          lambda self_btn, *arg: Result(self_btn.prev_button.prev_button,
                                                        f'Все сессии {el0} удалены'
                                                        if delete_session(username=el0)
                                                        else f'Ошибка удаления {el0} сессий')
                      ))())
               for el in get_my_account(chat_id)
           ] + [
               Button(f'{key}_all_session', 'Все', is_work=True,
                      work_def=lambda self_btn, *arg: Result(self_btn.prev_button.prev_button,
                                                       '\n'.join([
                                                           f'Все сессии {el[0]} удалены'
                                                           if delete_session(username=el[0])
                                                           else f'Ошибка удаления {el[0]} сессий'
                                                           for el in get_my_account(chat_id)
                                                       ])))
           ], analize=lambda x, chat_id, *args: None if len(x.get_keys(chat_id)) > 2 else Result(x.prev_button, 'У вас нет аккаунтов'))
])




