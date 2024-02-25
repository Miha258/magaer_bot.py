from aiogram import types
from config import roles

def get_admin_kb():
    keyboard = types.ReplyKeyboardMarkup(row_width = 2, resize_keyboard = True)
    buttons = [
        types.KeyboardButton('Статистика'),
        types.KeyboardButton('Создать менеджера'),
        types.KeyboardButton('Обновить баллы менеджера'),
        types.KeyboardButton('Установить время перерыва'),
        types.KeyboardButton('Установить рабочее время'),
        types.KeyboardButton('Обновить роль'),
        types.KeyboardButton('Создать команду'),
        types.KeyboardButton('Удалить команду'),
        types.KeyboardButton('Отправить сообщение в чаты'),
        types.KeyboardButton('Удалить менеджера')
    ]
    keyboard.add(*buttons)
    return keyboard

def get_roles_kb():
    keyboard = types.ReplyKeyboardMarkup(
    [
        [types.KeyboardButton(role)] for role in roles
    ],
    resize_keyboard = True
    )
    return keyboard

def get_teamlead_kb():
    keyboard = types.ReplyKeyboardMarkup(row_width = 2, resize_keyboard = True)
    buttons = [
        types.KeyboardButton('Добавить в команду'),
        types.KeyboardButton('Удалить из команды'),
        types.KeyboardButton('Статистика команды')
    ]
    keyboard.add(*buttons)
    return keyboard