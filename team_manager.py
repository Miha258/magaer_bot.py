from aiogram import types
from sqlalchemy import func
from config import *
from utils import *
from db import session, User, Team, Chat, WeeklyStats, DailyStats
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from keyboards import get_teamlead_kb

class Teams(StatesGroup):
    REMOVE_MEMBER = State()
    ADD_MEMBER = State()
    CHOOSE_STATS_TYPE = State()


async def show_team_statistics(message: types.Message):
    team_name = session.query(User).filter_by(id = message.from_id).first().team_id
    team = session.query(Team).filter_by(name=team_name).first()
    if team:
        members = session.query(User).filter_by(team_id=team.name).all()
        response = f"Статистика команды {team_name}:\n"
        for member in members:
            avrg_worktime = f"{int((member.average_reply_worktime / 60) // 60)} час. {int((member.average_reply_worktime / 60) % 60)} мин." if member.average_reply_worktime else "0 час. 0 мин." 
            avrg_time = f"{int((member.average_reply_time / 60) // 60)} час. {int((member.average_reply_time / 60) % 60)} мин." if member.average_reply_time else "0 час. 0 мин."
            braketime = ", <strong>Перерыв до: </strong>" + datetime.strftime(member.paused, "%Y.%m.%d-%H:%M") if member.paused > datetime.now() else ""
            response += f"{member.name}, <strong>Роль:</strong> {member.role}, <strong>ID:</strong> {member.id}, <strong>Баллы</strong>: {member.quality_score}, <strong>Команда:</strong> {'нет' if not member.team_id else member.team_id}, <strong>Рабочее время:</strong> {':'.join(str(member.start_work_at).split(':')[:-1])}-{':'.join(str(member.end_work_at).split(':')[:-1])}, <strong>Среднее время ответа в рабочее время:</strong> {avrg_worktime}, <strong>Среднее время ответа в нерабочее время:</strong> {avrg_time} {braketime}\n\n"
        await message.answer(response, parse_mode='html', reply_markup = get_teamlead_kb())
    else:
        await message.answer("Команда с таким именем не найдена.")


async def show_team_statistics_weekly(message: types.Message):
    team_name = session.query(User).filter_by(id = message.from_id).first().team_id
    team = session.query(Team).filter_by(name=team_name).first()
    if team:
        now = datetime.now()
        members = session.query(WeeklyStats).filter(
            WeeklyStats.start_day < now,
            WeeklyStats.end_day > now
        ).order_by(WeeklyStats.quality_score).all()
        response = f"Статистика команды {team_name}:\n"
        for member in members:
            user = session.query(User).filter_by(id = member.user_id).first()
            avrg_worktime = f"{int((member.average_reply_worktime / 60) // 60)} час. {int((member.average_reply_worktime / 60) % 60)} мин." if member.average_reply_worktime else "0 час. 0 мин." 
            avrg_time = f"{int((member.average_reply_time / 60) // 60)} час. {int((member.average_reply_time / 60) % 60)} мин." if member.average_reply_time else "0 час. 0 мин."
            if user:
                if user.team_id == team_name:
                    braketime = ", <strong>Перерыв до: </strong>" + datetime.strftime(user.paused, "%Y.%m.%d-%H:%M") if user.paused > datetime.now() else ""
                    response += f"{user.name}, <strong>Роль:</strong> {user.role}, <strong>ID:</strong> {user.id}, <strong>Баллы</strong>: {member.quality_score}, <strong>Команда:</strong> {'нет' if not user.team_id else user.team_id}, <strong>Рабочее время:</strong> {':'.join(str(user.start_work_at).split(':')[:-1])}-{':'.join(str(user.end_work_at).split(':')[:-1])}, <strong>Среднее время ответа в рабочее время:</strong> {avrg_worktime}, <strong>Среднее время ответа в нерабочее время:</strong> {avrg_time} {braketime}\n\n"
        await message.answer(response, parse_mode='html', reply_markup = get_teamlead_kb())
    else:
        await message.answer("Команда с таким именем не найдена.")


async def show_team_statistics_daily(message: types.Message):
    team_name = session.query(User).filter_by(id = message.from_id).first().team_id
    team = session.query(Team).filter_by(name=team_name).first()
    if team:
        members = session.query(DailyStats).filter(
            func.date(DailyStats.date) == datetime.now().date()
        ).order_by(DailyStats.quality_score).all()
        response = f"Статистика команды {team_name} за день:\n"
        for member in members:
            user = session.query(User).filter_by(id = member.user_id).first()
            avrg_worktime = f"{int((member.average_reply_worktime / 60) // 60)} час. {int((member.average_reply_worktime / 60) % 60)} мин." if member.average_reply_worktime else "0 час. 0 мин." 
            avrg_time = f"{int((member.average_reply_time / 60) // 60)} час. {int((member.average_reply_time / 60) % 60)} мин." if member.average_reply_time else "0 час. 0 мин."
            if user:
                if user.team_id == team_name:
                    braketime = ", <strong>Перерыв до: </strong>" + datetime.strftime(user.paused, "%Y.%m.%d-%H:%M") if user.paused > datetime.now() else ""
                    response += f"{user.name}, <strong>Роль:</strong> {user.role}, <strong>ID:</strong> {user.id}, <strong>Баллы</strong>: {member.quality_score}, <strong>Команда:</strong> {'нет' if not user.team_id else user.team_id}, <strong>Рабочее время:</strong> {':'.join(str(user.start_work_at).split(':')[:-1])}-{':'.join(str(user.end_work_at).split(':')[:-1])}, <strong>Среднее время ответа в рабочее время:</strong> {avrg_worktime}, <strong>Среднее время ответа в нерабочее время:</strong> {avrg_time} {braketime}\n\n"
        await message.answer(response, parse_mode='html', reply_markup = get_teamlead_kb())
    else:
        await message.answer("Команда с таким именем не найдена.")

async def add_member_to_team_command(message: types.Message):
    try:
        command_parts = message.text.split()
        team_name = session.query(User).filter_by(id = message.from_id).first().team_id
        user_id = command_parts[1]
        user = session.query(User).filter_by(name = user_id).first()
        team = session.query(Team).filter_by(name = team_name).first()

        if team:
            if user:
                if user.role == 'Тимлид':
                    return await message.answer('У вас нет доступа для добавления тимлида!')
                
                if user.team_id != None:
                    return await message.answer('Работник уже находиться в команде!')
                user.team_id = team.name
                session.commit()
                await message.answer(f"Пользователь с username {user_id} добавлен в команду {team_name}.")
            else:
                await message.answer("Пользователь с таким username не найден.")
        else:
            await message.answer("Команда с таким именем не найдена.")
    except IndexError:
        await message.answer('Неправильное количество аргументов.')

async def remove_member_from_team_command(message: types.Message):
    try:
        command_parts = message.text.split()
        team_name = session.query(User).filter_by(id = message.from_id).first().team_id
        user_id = command_parts[1]
        user = session.query(User).filter_by(name = user_id).first()
        team = session.query(Team).filter_by(name = team_name).first()
        if team:
            if user:
                if user.role == 'Тимлид':
                    return await message.answer('У вас нет доступа для удаления тимлида!')
                if user.team_id != team_name:
                    return await message.answer('Работник не в вашей команде!')
                user.team_id = None
                session.commit()
                await message.answer(f"Пользователь с username {user_id} удален из команды {team_name}.")
            else:
                await message.answer("Пользователь с таким username не найден.")
        else:
            await message.answer("Команда с таким именем не найдена.")
    except IndexError:
        await message.answer('Неправильное количество аргументов.')


async def add_bot_to_chat(message: types.Message):
    inviter_id = message.from_user.id
    if message.content_type == "new_chat_members":
        chat_id = message.chat.id
        user = session.query(User).filter_by(id = inviter_id).first()
        existing_chat = session.query(Chat).filter_by(chat_id=chat_id).first()
        if user:
            if user.role == 'Афф-менеджер' or user.role == 'Тимлид':
                if existing_chat:
                    await message.answer("Этот чат уже добавлен в базу данных.")
                else:
                    new_chat = Chat(chat_id = chat_id, team_id = user.team_id)
                    session.add(new_chat)
                    session.commit()
                    await message.answer("Чат успешно добавлен в базу данных.")
            else:
                await message.answer('У вас нет прав на добавления бота в чат!')
                await message.chat.leave()
        else:
            await message.answer('У вас нет прав на добавления бота в чат!')
            await message.chat.leave()
    elif message.content_type == "left_chat_members":
        session.delete(existing_chat)
        session.commit()
    

async def handle_user_option(message: types.Message, state: FSMContext):
    action = message.text
    await message.answer('Введите @username:')
    if action == 'Добавить в команду':
        await state.set_state(Teams.ADD_MEMBER)
    elif action == 'Удалить из команды':
        await state.set_state(Teams.REMOVE_MEMBER)
    elif action == 'Статистика команды':
        await message.answer('Выберите тип статистики', reply_markup = types.ReplyKeyboardMarkup(
            [
             [types.KeyboardButton('За месяц')],
             [types.KeyboardButton('За неделю')],
             [types.KeyboardButton('За день')]
            ], 
            resize_keyboard = True
        ))
        await state.set_state(Teams.CHOOSE_STATS_TYPE)



async def add_member_to_team(message: types.Message, state: FSMContext):
    team_name = session.query(User).filter_by(id = message.from_id).first().team_id
    user_id = message.text
    user = session.query(User).filter_by(name = user_id).first()
    team = session.query(Team).filter_by(name = team_name).first()
    if team:
        if user:
            if user.role == 'Тимлид':
                return await message.answer('У вас нет доступа для добавления тимлида!')
            
            if user.team_id != None:
                return await message.answer('Работник уже находиться в команде!')
            user.team_id = team.name
            session.commit()
            await state.finish()
            await message.answer(f"Пользователь с username {user_id} добавлен в команду {team.name}.")
        else:
            await message.answer("Пользователь с таким username не найден.")
    else:
        await message.answer("Команда с таким именем,как у вас,не найдена.")

async def remove_member_from_team(message: types.Message, state: FSMContext):
    team_name = session.query(User).filter_by(id = message.from_id).first().team_id
    user_id = message.text
    user = session.query(User).filter_by(name = user_id).first()
    team = session.query(Team).filter_by(name = team_name).first()
    if team:
        if user:
            if user.role == 'Тимлид':
                return await message.answer('У вас нет доступа для удаления тимлида!')
            
            if user.team_id != team_name:
                return await message.answer('Работник не в вашей команде!')
            user.team_id = None
            session.commit()
            await state.finish()
            await message.answer(f"Пользователь с username {user_id} удален из команды {team_name}.")
        else:
            await message.answer("Пользователь с таким username не найден.")
    else:
        await message.answer("Команда с таким именем,как у вас,не найдена.")


async def choose_statistic(message: types.Message, state: FSMContext):
    if message.text == 'За месяц':
        await show_team_statistics(message)
    elif message.text == 'За неделю':
        await show_team_statistics_weekly(message)
    elif  message.text == 'За день':
        await show_team_statistics_daily(message)
    await state.finish()

def register_teamlead(dp: Dispatcher):
    dp.register_message_handler(choose_statistic, state = Teams.CHOOSE_STATS_TYPE)
    dp.register_message_handler(show_team_statistics, IsTeamlead(), commands = ['team_stats'])
    dp.register_message_handler(show_team_statistics, IsTeamlead(), commands = ['team_stats_monthly'])
    dp.register_message_handler(show_team_statistics_weekly, IsTeamlead(), commands = ['team_stats_weeekly'])
    dp.register_message_handler(show_team_statistics_daily, IsTeamlead(), commands = ['team_stats_daily'])
    dp.register_message_handler(add_member_to_team_command, IsTeamlead(), commands=['add_member_to_team'])
    dp.register_message_handler(remove_member_from_team_command, IsTeamlead(), commands=['remove_member_from_team'])
    dp.register_message_handler(handle_user_option, IsTeamlead(), lambda m: m.text in ('Добавить в команду', 'Удалить из команды', 'Статистика команды'))
    dp.register_message_handler(add_member_to_team, IsTeamlead(), state = Teams.ADD_MEMBER)
    dp.register_message_handler(remove_member_from_team, IsTeamlead(), state = Teams.REMOVE_MEMBER)
    dp.register_message_handler(add_bot_to_chat, lambda m: m.new_chat_members[0].id == bot.id if m.new_chat_members else m.left_chat_member.id == bot.id if m.left_chat_member else False, content_types = types.ContentTypes.NEW_CHAT_MEMBERS | types.ContentTypes.LEFT_CHAT_MEMBER)