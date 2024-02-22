from aiogram import types
from config import *
from utils import *
from db import session, User, Chat, Team
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

class CreateUser(StatesGroup):
    USER_ROLE = State()
    MESSAGE = State()
    TEAM = State()

async def update_manager_score(message: types.Message):
    try:
        command_parts = message.text.split()
        user_id = command_parts[1]
        score_to_update = int(command_parts[2])
        user = session.query(User).filter_by(name = user_id).first()
        if user:
            session.add(User(name = user_id, score = user + score_to_update))
            session.commit()
    except IndexError:
        await message.answer('Неправильное количество аргументов')

async def show_department_statistics(message: types.Message):
    response = "Статистика отдела:\n"
    members = session.query(User).filter_by()
    for member in members:
        avrg_worktime = member.average_reply_worktime / 60 if member.average_reply_worktime else 0 
        avrg_time = member.average_reply_time / 60 if member.average_reply_time else 0
        braketime = ", <strong>Прерван до: </strong>" + datetime.strftime(member.paused, "%Y.%m.%d-%H:%M") if member.paused > datetime.now() else ""
        response += f"{member.name}, <strong>Роль:</strong> {member.role}, <strong>ID:</strong> {member.id}, <strong>Баллы</strong>: {member.quality_score}, <strong>Команда:</strong> {'нет' if not member.team_id else member.team_id}, <strong>Рабочее время:</strong> {':'.join(str(member.start_work_at).split(':')[:-1])}-{':'.join(str(member.end_work_at).split(':')[:-1])}, <strong>Сред.Рабочее:</strong> {avrg_worktime:.2f}мин, <strong>Сред.Нерабочее:</strong> {avrg_time:.2f}мин{braketime}\n\n"
    await message.answer(response, parse_mode = 'html')


async def send_message_to_department(message: types.Message):
    try:
        chats = session.query(Chat).all()
        command_parts = message.text.split()
        message_text = " ".join(command_parts[1:])
        counter = 0
        for chat in chats:
            try:
                await bot.send_message(chat.chat_id, message_text)
                counter += 1
            except Exception as e:
                print(f"Ошибка при отправке сообщения в чат {chat.chat_id}: {e}")
        await message.answer(f'Сообщения отправлено для <strong>{counter}</strong> чатов!', parse_mode = "html")
    except IndexError:
            await message.answer('Неправильное количество аргументов')

async def process_remove_manager_command_with_args(message: types.Message):
    try:
        command_parts = message.text.split()
        user_id = command_parts[1]
        date_str = command_parts[2]
        date = is_valid_date(date_str)
        if not user_id.isdigit():
            await message.answer("Неправильный формат username. username должен состоять только из цифр.")
        if not date:
            return await message.answer("Неправильный формат даты. Пожалуйста, используйте формат 'YYYY.MM.DD HH:MM'.")

        user = session.query(User).filter_by(telegram_id=user_id).first()
        if user:
            user.paused = datetime.datetime.now()
            session.commit()
            await message.answer(f"Менеджер с username @{user_id} удален.")
        else:
            await message.answer("Менеджер с таким username не найден.")
    except IndexError:
        await message.answer('Неправильное количество аргументов')

async def set_braketime(message: types.Message):
    try:
        command_parts = message.text.split()
        user_id = command_parts[1]
        date_str = command_parts[2]
        date = is_valid_date(date_str)
        if not date:
            return await message.answer("Неправильный формат даты. Пожалуйста, используйте формат 'YYYY.MM.DD-HH:MM'.")

        user = session.query(User).filter_by(name = user_id).first()
        if user:
            user.paused = date
            session.commit()
            await message.answer(f"Время перерыва для менеджера с username @{user_id} установлено.")
        else:
            await message.answer("Менеджер с таким username не найден.")
    except IndexError:
        await message.answer('Неправильное количество аргументов')

async def set_workday_range(message: types.Message):
    try:
        command_parts = message.text.split()
        user_id = command_parts[1]
        start_time = command_parts[2]
        end_time = command_parts[3]
        start_time = is_valid_time(start_time)
        end_time = is_valid_time(end_time)
        if not user_id.isdigit():
            await message.answer("Неправильный формат username. username должен состоять только из цифр.")
        if not start_time or not end_time:
            return await message.answer("Неправильный формат даты. Пожалуйста, используйте формат 'YYYY.MM.DD HH:MM'.")
        
        user = session.query(User).filter_by(name = user_id).first()
        if user:
            user.start_work_at = start_time
            user.end_work_at = end_time
            session.commit()
            await message.answer(f"Время для @{user.name} успешно установлено.")
        else:
            await message.answer("Менеджер с таким username не найден.")
    except IndexError:
        await message.answer('Неправильное количество аргументов')

async def update_user_role(message: types.Message):
    try:
        command_parts = message.text.split()
        user_id = command_parts[1]
        new_role = command_parts[2]

        if new_role not in roles:
            await message.answer(f'Роль должна быть из списка ({roles})')
        
        user = session.query(User).filter_by(name = user_id).first()
        if user:
            if user:
                user.role = new_role
                session.commit()
                await message.answer('Роль успешно обновлена')
            else:
                await message.answer('Пользователь не найден')
        else:
            await message.answer('Пользователь не найден')
    except IndexError:
        await message.answer('Неправильное количество аргументов')
    

async def create_manager(message: types.Message, state: FSMContext):
    kb = types.ReplyKeyboardMarkup(
    [
        [types.KeyboardButton(role)] for role in roles
    ],
    resize_keyboard = True
    )
    await message.answer('Выберите роль участника:', reply_markup = kb)
    await state.set_state(CreateUser.USER_ROLE)


async def recive_manager_data(message: types.Message, state: FSMContext):
    await state.set_data({'role': message.text})

    if message.text == 'Тимлид':
        print([[types.KeyboardButton(team.name)] for team in session.query(Team).all()])
        kb = types.ReplyKeyboardMarkup([[types.KeyboardButton(team.name)] for team in session.query(Team).all()], resize_keyboard = True)
        await message.answer('Выберите команду для тимлида:', reply_markup = kb)
        await state.set_state(CreateUser.TEAM)
    else:
        await message.answer('Перешлите сообщения из чата:')
        await state.set_state(CreateUser.MESSAGE)


async def set_manager_team(message: types.Message, state: FSMContext):
    await state.update_data({'team': message.text})
    await message.answer('Перешлите сообщения из чата:')
    await state.set_state(CreateUser.MESSAGE)

async def procces_create_manager(message: types.Message, state: FSMContext):
    if not message.forward_from:
        await message.answer('Попробуйте другое сообщения') 
    else:
        data = await state.get_data()
        chat_member = message.forward_from
        user = User(
            id = chat_member.id,
            name = "@" + chat_member.username,
            role = data['role'],
            team_id = data.get('team')
        )
        session.add(user)
        session.commit()
        await message.answer(f"{data['role']} успешно создан.")
        await state.finish()

async def remove_manager(message: types.Message):
    try:
        command_parts = message.text.split()
        user_id = command_parts[1]
        user = session.query(User).filter_by(name = user_id).first()
        if user:
            session.delete(user)
            session.commit()
            await message.answer(f'Менеджер успешно удален')
        else:
            await message.answer('Менеджера с таким айди не существует')
    except IndexError:
        await message.answer('Неправильное количество аргументов')


async def create_team(message: types.Message):
    try:
        command_parts = message.text.split()
        team_name = command_parts[1]
        team = session.query(Team).filter_by(name = team_name).first()
        if not team:
            team = Team(
                name = team_name
            )
            session.add(team)
            session.commit()
            await message.answer(f'Команда {team_name} успешно создана')
        else:
            await message.answer('Команда с таким именем уже существует')
    except IndexError:
        await message.answer('Неправильное количество аргументов')

async def remove_team(message: types.Message):
    try:
        command_parts = message.text.split()
        team_name = command_parts[1]
        team = session.query(Team).filter_by(name = team_name).first()
        if team:
            users = session.query(User).filter_by(team_id = team_name).all()
            for user in users:
                user.team_id = None
            
            chat = session.query(Chat).filter_by(team_id = team_name).first()
            try:
                await bot.send_message(chat.chat_id, f'Команда {team_name} удалена!')
                await bot.leave_chat(chat.chat_id)
            except:
                pass

            session.delete(chat)
            session.delete(team)
            session.commit()
            await message.answer(f'Команда {team_name} успешно удалена')
        else:
            await message.answer('Команда с таким именем не существует')
    except IndexError:
        await message.answer('Неправильное количество аргументов')


def register_admin(dp: Dispatcher):
    dp.register_message_handler(create_manager, IsAdmin(), commands = ['create_manager'])
    dp.register_message_handler(recive_manager_data, IsAdmin(), lambda m: m.text in roles, state = CreateUser.USER_ROLE)
    dp.register_message_handler(set_manager_team, lambda m: m.text in [team.name for team in session.query(Team).all()], state = CreateUser.TEAM)
    dp.register_message_handler(procces_create_manager, IsAdmin(), state = CreateUser.MESSAGE)
    dp.register_message_handler(remove_manager, IsAdmin(), commands = ['remove_manager'])
    dp.register_message_handler(update_manager_score, IsAdmin(), commands = ['update_manager_score'])
    dp.register_message_handler(show_department_statistics, IsAdmin(), commands = ['stats'])
    dp.register_message_handler(set_braketime, IsAdmin(), commands = ['set_braketime'])
    dp.register_message_handler(set_workday_range, IsAdmin(), commands = ['set_workday_range'])
    dp.register_message_handler(update_user_role, IsAdmin(), commands = ['update_role'])
    dp.register_message_handler(create_team, IsAdmin(), commands = ['create_team'])
    dp.register_message_handler(remove_team, IsAdmin(), commands = ['remove_team'])
    dp.register_message_handler(send_message_to_department, IsAdmin(), commands = ['send_message_to_chats'])