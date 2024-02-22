from aiogram import types
from config import *
from utils import *
from db import session, User, Team, Chat

async def show_team_statistics(message: types.Message):
    team_name = session.query(User).filter_by(id = message.from_id).first().team_id
    team = session.query(Team).filter_by(name=team_name).first()
    if team:
        members = session.query(User).filter_by(team_id=team.name).all()
        response = f"Статистика команды {team_name}:\n"
        for member in members:
            avrg_worktime = member.average_reply_worktime / 60 if member.average_reply_worktime else 0 
            avrg_time = member.average_reply_time / 60 if member.average_reply_time else 0
            braketime = ", <strong>Прерван до: </strong>" + datetime.strftime(member.paused, "%Y.%m.%d-%H:%M") if member.paused > datetime.now() else ""
            response += f"{member.name}, <strong>Роль:</strong> {member.role}, <strong>ID:</strong> {member.id}, <strong>Баллы</strong>: {member.quality_score}, <strong>Команда:</strong> {'нет' if not member.team_id else member.team_id}, <strong>Рабочее время:</strong> {':'.join(str(member.start_work_at).split(':')[:-1])}-{':'.join(str(member.end_work_at).split(':')[:-1])}, <strong>Сред.Рабочее:</strong> {avrg_worktime:.2f}мин, <strong>Сред.Нерабочее:</strong> {avrg_time:.2f}мин{braketime}\n\n"
        await message.answer(response, parse_mode='html')
    else:
        await message.answer("Команда с таким именем не найдена.")

async def add_member_to_team(message: types.Message):
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
                await message.answer(f"Пользователь с username @{user_id} добавлен в команду {team_name}.")
            else:
                await message.answer("Пользователь с таким username не найден.")
        else:
            await message.answer("Команда с таким именем не найдена.")
    except IndexError:
        await message.answer('Неправильное количество аргументов.')

async def remove_member_from_team(message: types.Message):
    try:
        command_parts = message.text.split()
        team_name = team_name = session.query(User).filter_by(id = message.from_id).first().team_id
        user_id = command_parts[1]
        user = session.query(User).filter_by(name=user_id).first()
        team = session.query(Team).filter_by(name=team_name).first()
        if team:
            if user:
                if user.role == 'Тимлид':
                    return await message.answer('У вас нет доступа для удаления тимлида!')
                
                if user.team_id != team_name:
                    return await message.answer('Работник не в вашей команде!')
                user.team_id = None
                session.commit()
                await message.answer(f"Пользователь с username @{user_id} удален из команды {team_name}.")
            else:
                await message.answer("Пользователь с таким username не найден.")
        else:
            await message.answer("Команда с таким именем не найдена.")
    except IndexError:
        await message.answer('Неправильное количество аргументов.')


async def add_bot_to_chat(message: types.Message):
    inviter_id = message.from_user.id
    if message.content_type == "new_chat_members":
        chat_id = message.chat.shifted_id
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
    
def register_teamlead(dp: Dispatcher):
    dp.register_message_handler(show_team_statistics, IsTeamlead(), commands=['team_stats'])
    dp.register_message_handler(add_member_to_team, IsTeamlead(), commands=['add_member_to_team'])
    dp.register_message_handler(remove_member_from_team, IsTeamlead(), commands=['remove_member_from_team'])
    dp.register_message_handler(add_bot_to_chat, lambda m: m.new_chat_members[0].id == bot.id if m.new_chat_members else m.left_chat_member.id == bot.id if m.left_chat_member else False, content_types = types.ContentTypes.NEW_CHAT_MEMBERS | types.ContentTypes.LEFT_CHAT_MEMBER)