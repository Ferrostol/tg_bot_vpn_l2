from prettytable import PrettyTable, TableStyle

# Подключаем самописную библиотеку для кнопок
from butnlib.buttons import ButtonFixed, ButtonCustoms, ButtonWork, BaseButton
from butnlib.botLogic import Result

# Модули бота
import database
import server
import config
import logic


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


def check_admin(chat_id: int):
    return database.get_role_user(chat_id) == "admin"

start_buttons = ButtonFixed(key='start', caption='Начало', text='Выберите действие', buttons=[
    ButtonFixed(key='admin_tg', caption='Админ TG', text='Выберите действие', can_back=True, visible=lambda chat_id: check_admin(chat_id), buttons=[
        ButtonCustoms(key='unlock', caption='Дать доступ пользователю TG', text='Выберите пользователя для разблокировки', can_back=True,
               def_for_buttons=lambda key, *args: [
                   ButtonWork(key=el[0], caption=el[1], work_def=(lambda el0=el[0], el1=el[1]: (
                       lambda self_btn, chat_id, *arg: (
                           Result(self_btn.get_prev_button(chat_id=chat_id, two_up=True),
                                  "Пользователь разблокирован"
                                  if database.enable_user_tg(el0, 1) == 'edit'
                                  else f"Ошибка при разблокировке пользователя {el1}")
                       )))())
                   for el in database.get_all_tg_username(enabled=0)
               ], analyze=lambda x, *args: None if len(database.get_all_tg_username(enabled=0)) > 0 else Result(x.prev_button, 'Пользователей нет')),

        ButtonCustoms(key='delete', caption='Удалить пользователя TG', text='Выберите пользователя для удаления', can_back=True,
               def_for_buttons=lambda key, *args: [
                   ButtonWork(key=el[0], caption=el[1], is_work=True, work_def=(lambda el0=el[0], el1=el[1]: (
                       lambda self_btn, chat_id, *arg: (
                           Result(self_btn.get_prev_button(chat_id=chat_id, two_up=True),
                                  "Пользователь удален"
                                  if database.delete_tg_user(el0) == 'edit'
                                  else f"Ошибка при удалении пользователя {el1}")
                       )))())
                   for el in database.get_all_tg_username()
               ], analyze=lambda x, *args: None if len(database.get_all_tg_username()) > 0 else Result(x.prev_button, 'Пользователей нет')),

        ButtonCustoms(key='lock', caption='Заблокировать пользователя TG', text='Выберите пользователя для блокировки', can_back=True,
               def_for_buttons=lambda key, *args: [
                   ButtonWork(key=el[0], caption=el[1], is_work=True, work_def=(lambda el0=el[0], el1=el[1]: (
                       lambda self_btn, chat_id, *arg: (
                           Result(self_btn.get_prev_button(chat_id=chat_id, two_up=True),
                                  "Пользователь заблокирован"
                                  if database.enable_user_tg(el0, 0) == 'edit'
                                  else f"Ошибка при блокировке пользователя {el1}")
                       )))())
                   for el in database.get_all_tg_username(enabled=1)
               ], analyze=lambda x, *args: None if len(database.get_all_tg_username(enabled=1)) > 0 else Result(x.prev_button, 'Пользователей нет')),

        ButtonWork(key='show_users', caption='Посмотреть пользователей TG', can_back=True, parse_mode="markdown",
               work_def=lambda self, chat_id, *arg: (
                   Result(self.prev_button, "Список пользователей пуст")
                   if not len((data := database.get_all_tg_username()))
                   else Result(self, get_table_str(['USR_ID', 'NAME', 'ROLE', 'ENABLED'], data))
                ))
    ]),

    ButtonCustoms(key='admin_serv', caption='Админ VPN серверов', text='Выберите сервер', visible=lambda chat_id: check_admin(chat_id), can_back=True, get_first_if_one=True,
           def_for_buttons= lambda *args: [
               ButtonFixed(key=f'srv_{srv[0]}', caption=srv[1], text=f'Сервер {srv[1]}', can_back=True, buttons=[
                   *[
                       ButtonWork(key=f'add_user_vpn_{ind}', caption=cap, can_back=True,
                          work_def=lambda self, chat_id, *arg, server_id=srv[0], indx=ind: Result(
                              self, 'Введите имя нового пользователя', make_recursive_lambda(lambda self_func, login, *args: (
                                  Result(BaseButton.get_buttons(start_buttons, chat_id, self.keys_search),'Ошибка создания пользователя')
                                  if not check_admin(chat_id)
                                  else Result(self, "Введите пароль для пользователя", make_recursive_lambda(lambda self_func_pass, password, *args_2: (
                                      Result(BaseButton.get_buttons(start_buttons, chat_id, self.keys_search), 'Ошибка создания пользователя')
                                      if not check_admin(chat_id)
                                      else Result(self.prev_button, f'Пользователь создан\nЛогин:{login}\nПароль:{password}\nОбщий ключ:{server.get_ipsec_key()}')
                                      if (
                                          database.add_user(login, password, server_id, indx),
                                          server.write_users_to_file([(el[0], el[1], el[3]) for el in database.get_all_username_vpn(server=server_id, enabled=1)], server=server_id),
                                          len([el for el in database.get_all_username_vpn(server=server_id) if el[0] == login])
                                      )[-1] > 0
                                      else Result(self.prev_button, "Пользователь не создан")
                                  )))
                                  if len([el for el in database.get_all_username_vpn(server=server_id) if el[0] == login]) == 0
                                  else Result(self, "Такой пользователь уже существует. Введите имя нового пользователя", self_func)
                              ))
                          ))
                       for ind, cap in ((0, 'Добавить пользователя VPN'), (1, 'Добавить сквозного пользователя VPN'))
                   ],

                   ButtonCustoms(key='unlock_vpn', caption='Разблокировать пользователя VPN', text='Выберите пользователя для разблокировки', can_back=True,
                          def_for_buttons=lambda key, *args, server_id=srv[0]: [
                                  ButtonWork(key=el[0], caption=el[0], work_def=(lambda el0=el[0], el1=el[1]: (
                                  lambda self_btn, chat_id, *arg: (
                                      Result(self_btn.get_prev_button(chat_id=chat_id, two_up=True),
                                             f"Ошибка при разблокировки пользователя {el1}"
                                             if not database.enable_user_vpn(el0, 1, server_id) == 'edit'
                                             else "Пользователь разблокирован"
                                             if (err := server.write_users_to_file([(els[0], els[1], els[3]) for els in database.get_all_username_vpn(server=server_id, enabled=1)], server=server_id)) is None
                                             else f"Ошибка при разблокировки пользователя {el1}. Ошибка {err}")
                                  )))())
                              for el in database.get_all_username_vpn(server=server_id, enabled=0)
                          ], analyze=lambda x, *args, server_id=srv[0]: None if len(database.get_all_username_vpn(server=server_id, enabled=0)) > 0 else Result(x.prev_button, 'Пользователей нет')),

                   ButtonCustoms(key='lock_vpn', caption='Заблокировать пользователя VPN', text='Выберите пользователя для блокировки', can_back=True,
                          def_for_buttons=lambda key, *args, server_id=srv[0]: [
                              ButtonWork(key=el[0], caption=el[0], work_def=(lambda el0=el[0], el1=el[1]: (
                                  lambda self_btn, chat_id, *arg: (
                                      Result(self_btn.get_prev_button(chat_id=chat_id, two_up=True),
                                             f"Ошибка при блокировке пользователя {el1}"
                                             if not database.enable_user_vpn(el0, 0, server_id) == 'edit'
                                             else "Пользователь заблокирован"
                                             if (err := server.write_users_to_file([(els[0], els[1], els[4]) for els in database.get_all_username_vpn(enabled=1)], server=server_id)) is None
                                             else f"Ошибка при блокировке пользователя {el1}. Ошибка {err}")
                                  )))())
                              for el in database.get_all_username_vpn(server=server_id, enabled=1)
                          ], analyze=lambda x, *args, server_id=srv[0]: None if len(database.get_all_username_vpn(server=server_id, enabled=1)) > 0 else Result(x.prev_button, 'Пользователей нет')),

                   ButtonCustoms(key='delete_vpn', caption='Удалить пользователя VPN', text='Выберите пользователя для удаления', can_back=True,
                          def_for_buttons=lambda key, *args, server_id=srv[0]: [
                              ButtonWork(key=el[0], caption=el[0], work_def=(lambda el0=el[0]: (
                                  lambda self_btn, chat_id, *arg: (
                                      Result(self_btn.get_prev_button(chat_id=chat_id, two_up=True),
                                             f"Ошибка при удалении пользователя {el0}"
                                             if not database.delete_vpn_user(el0, server_id) == 'edit'
                                             else "Пользователь удален"
                                             if (err := server.write_users_to_file([(els[0], els[1], els[4]) for els in database.get_all_username_vpn(enabled=1)], server=server_id)) is None
                                             else f"Пользователь удален. Ошибка при обновлении файла с доступами. Ошибка {err}")
                                  )))())
                              for el in database.get_all_username_vpn(server=server_id)
                          ], analyze=lambda x, *args, server_id=srv[0]: None if len(database.get_all_username_vpn(server=server_id)) > 0 else Result(x.prev_button, 'Пользователей нет')),

                   ButtonWork(key='del_all_ses', caption='Удалить все сессии',
                          work_def=lambda self, *arg, server_id=srv[0]: Result(
                              self.prev_button,
                              'Все сессии удалены' if server.delete_session(server=server_id) else 'Ошибка удаления сессий'
                          )),
                   ButtonWork(key='show_all_ses', caption='Посмотреть текущие сессии', can_back=True, parse_mode="markdown",
                          work_def=lambda self, chat_id, *arg, server_id=srv[0]: (
                              Result(self.prev_button, "Список сессий пуст")
                              if not len((data := server.get_all_processes(server=server_id)))
                              else Result(self, get_table_str(['PID', 'Local IP', 'Name'], data))
                          ), buttons=[
                           ButtonWork(key='reload', caption='Обновить', can_back=True, parse_mode="markdown",
                                  work_def=lambda self, *arg: self.prev_button.work_def(self.prev_button, *arg))
                       ]),
                   ButtonWork(key='vpn_users', caption='Посмотреть пользователей VPN', can_back=True, parse_mode="markdown",
                          work_def=lambda self, chat_id, *arg, server_id=srv[0]: (
                              Result(self.prev_button, "Список пользователей пуст")
                              if not len((data := database.get_all_username_vpn(server=server_id)))
                              else Result(self, get_table_str(['USR', 'PASSWORD', 'STATUS', 'COMBINE'], data))
                          ))
               ]) for srv in database.get_all_servers()
           ], analyze=lambda x, chat_id, *args: None if database.get_count_servers() > 0 else Result(x.get_prev_button(chat_id=chat_id), 'Отсутствуют сервера VPN')),

    ButtonFixed(key='settings', caption='Настройки', text='Выберите действие', visible=lambda chat_id: check_admin(chat_id), can_back=True, buttons= [
        ButtonCustoms(key='multi_connect', caption='1 user != 1 session', text='Изменение', can_back=True, def_for_buttons= lambda *args : [
            ButtonFixed(key='enable', caption='Выключить' if config.multi_connect else 'Включить', text='Подтвердите', can_back=True, buttons=[
                ButtonWork(key=name, caption='Подтвердаю', visible=lambda *args, visibled=visible_: visibled,
                       work_def=(lambda enabled_=config.multi_connect: (
                           lambda self_btn, chat_id, *args: (
                               Result(
                                   self_btn.get_prev_button(chat_id=chat_id, two_up=True).get_prev_button(chat_id=chat_id),
                                   'Настройка изменена'
                                   if (err := server.edit_multi_connect(not enabled_)) is None
                                   else err
                               )
                           )))())
                for name, visible_ in zip(['on', 'off'], [not config.multi_connect, config.multi_connect])
            ])
        ]),
        ButtonFixed(key='update_bot', caption='Обновить бота', can_back=True, buttons=[
            ButtonWork(key='confirm', caption='100% Да', work_def= lambda self_btn, chat_id, bot, *args: server.update_bot(bot))
        ]),
        ButtonFixed(key='export_db', caption='Экспорт БД', can_back=True, buttons=[
            ButtonWork(key='confirm', caption='100% Да',
                   work_def= lambda self_btn, chat_id, bot, *args: (
                       Result(self_btn.get_prev_button(chat_id=chat_id, two_up=True),
                              (logic.send_file(bot, chat_id, config.database_file), 'Файл экспортирован')[-1])
                   ))
        ]),
        ButtonFixed(key='import_bd', caption='Импорт БД', can_back=True, buttons=[
            ButtonWork(key='confirm', caption='100% Да', can_back=True, work_def= lambda self_btn, chat_id, bot, *args: (
                Result(self_btn, 'Пришлите файл БД', make_recursive_lambda(lambda self_func, _, __, message, *args_1: (
                    Result(self_btn, 'Некорректный файл', self_func)
                    if not message.document
                    else (logic.get_file_and_save(bot, message, f"{config.database_file}"), server.write_users_to_file([(els[0], els[1], els[4]) for els in database.get_all_username_vpn(enabled=1)]), server.restart_bot(bot))
                ))))
            )
        ]),
        ButtonFixed(key='update_file_users', caption='Обновить пользователей VPN', can_back=True, buttons=[
            ButtonWork(key='confirm', caption='100% Да', can_back=True, work_def= lambda self_btn, *args: (
                Result(self_btn, "Файл с пользователям обновлен"
                                  if (err := server.write_users_to_file([(els[0], els[1], els[4]) for els in database.get_all_username_vpn(enabled=1)])) is None
                                  else f"Ошибка при обновлении файла с доступами. Ошибка {err}")
            ))
        ])
    ]),

    ButtonWork(key='show_my_acc', caption='Посмотреть свои аккаунты', can_back=True, parse_mode="markdown",
           work_def=lambda self, chat_id, *arg: (
               Result(self.prev_button, "Список пользователей пуст")
               if not len((data := database.get_my_account(chat_id)))
               else Result(self, get_table_str(['USR', 'PASSWORD'], data))
           )),

    ButtonWork(key='connect_acc', caption='Привязать аккаунт', can_back=True,
           work_def=lambda self, chat_id, *arg: Result(
               self, 'Введите имя нового пользователя', make_recursive_lambda(lambda self_func, login, *args: (
                   Result(self, "Введите пароль для пользователя", make_recursive_lambda(lambda self_func_pass, password, *args_2: (
                       Result(self.prev_button, 'Аккаунт привязан к вам' if database.connect_tg_vpn(chat_id, login) == 'edit' else 'Ошибка привязки аккаунта')
                       if len([el for el in database.get_all_username_vpn() if el[0] == login and el[1] == password]) > 0
                       else Result(self, "Неверные данные входа, начните заново", self_func)
                   )))
                   if len([el for el in database.get_my_account(chat_id) if el[0] == login]) == 0
                   else Result(self, "Данный аккаунт уже привязан к вам", self_func)
               ))
           )),

    ButtonCustoms(key='unconnect_acc', caption='Отвязать аккаунт', text='Выберете аккаунт для отвязки', can_back=True,
           def_for_buttons=lambda key, chat_id, *args: [
               ButtonWork(key=el[0], caption=el[0],
                      work_def=(lambda el0=el[0]: (
                          lambda self_btn, *arg: Result(self_btn.prev_button.prev_button,
                                                        f'Аккаунт отвязан'
                                                        if database.unconnect_user(chat_id, el0) == 'edit'
                                                        else f'Ошибка отвязки аккаунта')
                      ))())
               for el in database.get_my_account(chat_id)
           ], analyze=lambda x, chat_id, *args: None if len(database.get_my_account(chat_id)) > 0 else Result(x.prev_button, 'У вас нет аккаунтов')),

    ButtonCustoms(key='del_my_ses', caption='Удалить свои сессии', text='Выберете аккаунт для которого необходимо сбросить сессии', can_back=True,
           def_for_buttons=lambda key, chat_id, *args: [
               ButtonWork(key=el[0], caption=el[0],
                      work_def=(lambda el0=el[0]: (
                          lambda self_btn, *arg: Result(self_btn.prev_button.prev_button,
                                                        f'Все сессии {el0} удалены'
                                                        if server.delete_session(username=el0)
                                                        else f'Ошибка удаления {el0} сессий')
                      ))())
               for el in database.get_my_account(chat_id)
           ] + [
               ButtonWork(key='_all_session', caption='Все',
                      work_def=lambda self_btn, *arg: Result(self_btn.prev_button.prev_button,
                                                       '\n'.join([
                                                           f'Все сессии {el[0]} удалены'
                                                           if server.delete_session(username=el[0])
                                                           else f'Ошибка удаления {el[0]} сессий'
                                                           for el in database.get_my_account(chat_id)
                                                       ])))
           ], analyze=lambda x, chat_id, *args: None if len(x.get_keys(chat_id)) > 2 else Result(x.prev_button, 'У вас нет аккаунтов'))
])








