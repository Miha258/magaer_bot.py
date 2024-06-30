import threading
from aiogram.utils import executor
from aiogram import types
from config import dp
from admin import register_admin
from db import create_tables
from config import admins
from db import User, session
from tracker import register_tracker
from team_manager import register_teamlead
from quality_manager import register_quality_manager
from manager import register_aff_manager
from aiogram.dispatcher import FSMContext
from keyboards import *
from scheduler import Scheduler
import time, datetime


@dp.message_handler(commands=['start'], state = '*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.username in admins:
        help_text = """
Список доступных команд:

/create_manager - создать менеджера
Пример использования: /create_manager

/remove_manager - удалить менеджера
Параметры: /remove_manager <username>
Пример использования: /remove_manager @username


/update_manager_score - обновить баллы
Параметры: /update_manager_score <username> <число>
Пример использования: /update_manager_score @user 3 или -3

/stats - просмотр статистики отдела
Пример использования: /stats

/monthly_stats -  просмотр статистики отдела (за месяц)
Пример использования: /monthly_stats

/weekly_stats -  просмотр статистики отдела (за неделю)
Пример использования: /weekly_stats

/daily_stats -  просмотр статистики отдела (за день)
Пример использования: /daily_stats

/set_braketime - установить время перерыва для менеджера
Параметры: /set_braketime <username> <дата>
Пример использования: /set_braketime @username 2024.02.15-14:30

/set_workday_range - установить рабочее время для менеджера
Параметры: /set_workday_range @user <время_начала> <время_конца>
Пример использования: /set_workday_range @username 09:00 18:00

/update_role - обновить роль пользователя
Параметры: /update_role <username> <новая_роль>
Пример использования: /update_role @username Тимлид

/create_team - создать команду
Параметры: /create_team <имя_команды>
Пример использования: /create_team Команда1

/remove_team - удалить команду
Параметры: /remove_team <имя_команды> (Тимлид, Афф-менеджер, Кволити-менеджер)
Пример использования: /remove_team Команда1

/send_message_to_chats - переслать сообщение по всем чатам
Параметры: /send_message_to_chats <текст>
Пример использования: /send_message_to_chats всем привет
        """
        await message.answer(help_text, reply_markup = get_admin_kb())
    else:
        user = session.query(User).filter_by(id = message.from_id).first()
        if user:
            if user.role == 'Тимлид':
                await message.answer("""
Список доступных команд:

/team_stats - показать статистику команды.
Например: /team_stats
                                     
/team_stats_monthly -  просмотр статистики команды (за месяц)
Пример использования: /team_stats_monthly

/team_stats_weeekly -  просмотр статистики команды (за неделю)
Пример использования: /team_stats_weeekly
                                     
/team_stats_daily -  просмотр статистики команды (за день)
Пример использования: /team_stats_daily

/add_member_to_team <username> - добавить пользователя в команду.
Например: /add_member_to_team @username

/remove_member_from_team <username> - удалить пользователя из команды.
Например: /remove_member_from_team @username
    """, reply_markup = get_teamlead_kb())
            elif user.role == 'Кволити-менеджер':
                await message.answer("""
/stats - просмотр статистики отдела.
Например: /stats
                                     
/monthly_stats -  просмотр статистики отдела (за месяц)
Пример использования: /monthly_stats

/weekly_stats -  просмотр статистики отдела (за неделю)
Пример использования: /weekly_stats
                                     
/daily_stats -  просмотр статистики отдела (за день)
Пример использования: /daily_stats
    """)    
            elif user.role == 'Афф-менеджер':
                await message.answer("""
/personal_stats - персональной статистики.
Например: /personal_stats
(Так же есть возможность добаить бота в чат)
    """)


@dp.message_handler(text = 'Назад', state = '*')
async def back_to_admin_menu(message: types.Message, state: FSMContext):
    await message.answer('Меню:', reply_markup = get_admin_kb())
    await state.finish()


def update_stats():
    today = datetime.datetime.now()
    if today.day == 1:
        for user in session.query(User).all():
            user.average_reply_time = 0
            user.average_reply_worktime = 0
            user.quality_score = 100
        session.commit()


schedule = Scheduler()
schedule.daily(datetime.time(minute = 1), update_stats)

def run_tasks():
    while True:
        schedule.exec_jobs()
        time.sleep(1)

if __name__ == '__main__':
    register_admin(dp)
    register_teamlead(dp)
    register_aff_manager(dp)
    register_quality_manager(dp)
    register_tracker(dp)
    create_tables()
    threading.Thread(target = lambda: run_tasks()).start()
    executor.start_polling(dp, skip_updates = True)