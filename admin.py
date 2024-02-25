from aiogram import types
from config import *
from utils import *
from db import session, User, Chat, Team
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from keyboards import *


class CreateUser(StatesGroup):
    USER_ROLE = State()
    MESSAGE = State()
    TEAM = State()


class Users(StatesGroup):
    SET_USER = State()
    SET_SCORE = State()
    SET_BRAKETIME = State()
    SET_WORKDAY = State()
    SET_ROLE = State()
    ADD_TEAM = State()
    REMOVE_TEAM = State()
    REMOVE_MANAGER = State()
    CHAT_MESSAGE = State()


async def handle_user_option(message: types.Message, state: FSMContext):
    await state.finish()
    option = message.text
    match option:
        case 'Статистика':
            await show_department_statistics(message)
        case 'Создать команду':
            await state.set_state(Users.ADD_TEAM)
            await message.answer('Введите название команды:')
        case 'Удалить команду':
            await state.set_state(Users.REMOVE_TEAM)
            await message.answer('Введите название команды:')
        case 'Отправить сообщение в чаты':
            await state.set_state(Users.CHAT_MESSAGE)
            await message.answer('Введите сообщения для отправки:')
        case 'Создать менеджера':
            await create_manager(message, state)

async def set_user(message: types.Message, state: FSMContext):
    await state.finish()
    await state.set_data({'action': message.text})
    await state.set_state(Users.SET_USER)
    await message.answer('Введите @username:')
    

async def procces_action_with_user(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['username'] = message.text
        action = data['action']
        match action:
            case 'Обновить баллы менеджера':
                await state.set_state(Users.SET_SCORE)
                await message.answer('Введите сумму баллов:')
            case 'Установить время перерыва':
                await state.set_state(Users.SET_BRAKETIME)
                await message.answer('Введите время в формате <strong>01:00-22:00</strong>:', parse_mode = 'html')
            case 'Установить рабочее время':
                await state.set_state(Users.SET_WORKDAY)
                await message.answer('Введите дату в формате <strong>2024.02.28-20:15</strong>:', parse_mode = 'html')
            case 'Обновить роль':
                await state.set_state(Users.SET_ROLE)
                await message.answer('Введите @username:')
            case 'Удалить менеджера':
                await remove_manager(message, state, message.text)

async def create_team(message: types.Message, state: FSMContext):
    team_name = message.text
    team = session.query(Team).filter_by(name = team_name).first()
    if not team:
        team = Team(
            name = team_name
        )
        session.add(team)
        session.commit()
        await state.finish()
        await message.answer(f'Команда {team_name} успешно создана')
    else:
        await message.answer('Команда с таким именем уже существует. Пожалуйста, попробуйте еще раз:')


async def remove_team(message: types.Message, state: FSMContext):
    team_name = message.text
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
        await state.finish()
        await message.answer(f'Команда {team_name} успешно удалена')
    else:
        await message.answer('Команда с таким именем не существует. Пожалуйста, попробуйте еще раз:')


async def set_score(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        score_to_update = int(message.text)
        user = session.query(User).filter_by(name = data["username"]).first()
        if user:
            session.add(User(name = data["username"], quality_score = user.quality_score + score_to_update))
            session.commit()
            await state.finish()
            await message.answer(f'Сумма баллов для {data["username"]} успешно изменена')
    except ValueError:
        await message.answer('Неверное количество баллов')


async def set_braketime(message: types.Message, state: FSMContext):
    data = await state.get_data()
    date_str = message.text
    date = is_valid_date(date_str)
    if not date:
        return await message.answer("Неправильный формат даты. Пожалуйста, используйте формат 'YYYY.MM.DD-HH:MM'.")
    user = session.query(User).filter_by(name = data['username']).first()
    if user:
        user.paused = date
        session.commit()
        await state.finish()
        await message.answer(f"Время перерыва для менеджера с username {data['username']} установлено.")
    else:
        await message.answer("Менеджер с таким username не найден.")


async def set_workday_range(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        time_parts = message.text.split('-')
        start_time = time_parts[0]
        end_time = time_parts[1]
        start_time = is_valid_time(start_time)
        end_time = is_valid_time(end_time)

        if not start_time or not end_time:
            return await message.answer("Неправильный формат даты. Пожалуйста, используйте формат 'YYYY.MM.DD HH:MM'.")
        
        user = session.query(User).filter_by(name = data['username']).first()
        if user:
            user.start_work_at = start_time
            user.end_work_at = end_time
            session.commit()
            await state.finish()
            await message.answer(f"Время для {user.name} успешно установлено.")
        else:
            await message.answer("Менеджер с таким username не найден.")
    except IndexError:
        await message.answer('Неправильный формат даты. Пожалуйста, попробуйте еще раз:')


async def set_role(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_role = message.text
    
    if new_role not in roles:
        await message.answer(f'Роль должна быть из списка ({roles})')
    
    user = session.query(User).filter_by(name = data['username']).first()
    if user:
        if user:
            user.role = new_role
            session.commit()
            await state.finish()
            await message.answer('Роль успешно обновлена')
        else:
            await message.answer('Пользователь не найден')
    else:
        await message.answer('Пользователь не найден')


async def send_message_to_department(message: types.Message, state: FSMContext):
    await state.finish()
    chats = session.query(Chat).all()
    message_text = message.text
    counter = 0
    for chat in chats:
        try:
            await bot.send_message(chat.chat_id, message_text)
            counter += 1
        except Exception as e:
            print(f"Ошибка при отправке сообщения в чат {chat.chat_id}: {e}")
    await message.answer(f'Количество отправленных сообщений: <strong>{counter}</strong>', parse_mode = "html")
   

async def remove_manager(message: types.Message, state: FSMContext, username: str):
    user = session.query(User).filter_by(name = username).first()
    if user:
        session.delete(user)
        session.commit()
        await state.finish()
        await message.answer(f'Менеджер успешно удален')
    else:
        await message.answer('Менеджера с таким ID не существует')


async def update_manager_score_command(message: types.Message):
    try:
        command_parts = message.text.split()
        user_id = command_parts[1]
        score_to_update = int(command_parts[2])
        user = session.query(User).filter_by(name = user_id).first()
        if user:
            session.add(User(name = user_id, quality_score = user.quality_score + score_to_update))
            session.commit()
            await message.answer(f'Сумма баллов для {user.name} успешно изменена')
    except IndexError:
        await message.answer('Неправильное количество аргументов')
    except ValueError:
        await message.answer('Неверное количество баллов')


async def show_department_statistics(message: types.Message):
    response = "Статистика отдела:\n"
    members = session.query(User).order_by(User.quality_score).all()
    for member in members:
        avrg_worktime = member.average_reply_worktime / 60 if member.average_reply_worktime else 0 
        avrg_time = member.average_reply_time / 60 if member.average_reply_time else 0
        braketime = ", <strong>Перерыв до: </strong>" + datetime.strftime(member.paused, "%Y.%m.%d-%H:%M") if member.paused > datetime.now() else ""
        response += f"{member.name}, <strong>Роль:</strong> {member.role}, <strong>ID:</strong> {member.id}, <strong>Баллы</strong>: {member.quality_score}, <strong>Команда:</strong> {'нет' if not member.team_id else member.team_id}, <strong>Рабочее время:</strong> {':'.join(str(member.start_work_at).split(':')[:-1])}-{':'.join(str(member.end_work_at).split(':')[:-1])}, <strong>Среднее время рабочего:</strong> {avrg_worktime:.2f}мин, <strong>Среднее время ответа:</strong> {avrg_time:.2f}мин{braketime}\n\n"
    await message.answer(response, parse_mode = 'html')


async def send_message_to_department_command(message: types.Message):
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
        await message.answer(f'Количество отправленных сообщений: <strong>{counter}</strong>', parse_mode = "html")
    except IndexError:
            await message.answer('Неправильное количество аргументов')


async def set_braketime_command(message: types.Message):
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
            await message.answer(f"Время перерыва для менеджера с username {user_id} установлено.")
        else:
            await message.answer("Менеджер с таким username не найден.")
    except IndexError:
        await message.answer('Неправильное количество аргументов')


async def set_workday_range_command(message: types.Message):
    try:
        command_parts = message.text.split()
        user_id = command_parts[1]
        start_time = command_parts[2]
        end_time = command_parts[3]
        start_time = is_valid_time(start_time)
        end_time = is_valid_time(end_time)
        if not user_id.isdigit():
            await message.answer("Неправильный формат username. Username должен состоять только из цифр.")
        if not start_time or not end_time:
            return await message.answer("Неправильный формат даты. Пожалуйста, используйте формат 'YYYY.MM.DD HH:MM'.")
        
        user = session.query(User).filter_by(name = user_id).first()
        if user:
            user.start_work_at = start_time
            user.end_work_at = end_time
            session.commit()
            await message.answer(f"Время для {user.name} успешно установлено.")
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
    await message.answer('Выберите роль участника:', reply_markup = get_roles_kb())
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
        user = session.query(User).filter_by(id = chat_member.id).first()
        if not user:
            user = User(
                id = chat_member.id,
                name = "@" + chat_member.username,
                role = data['role'],
                team_id = data.get('team')
            )
            session.add(user)
            session.commit()
            await message.answer(f"{data['role']} успешно создан.", reply_markup = get_admin_kb())
            await state.finish()
        else:
            await message.answer('Менеджер уже зарегистрирован. Пожалуйста, попробуйте другого пользователя:')
        

async def remove_manager_command(message: types.Message):
    try:
        command_parts = message.text.split()
        user_id = command_parts[1]
        user = session.query(User).filter_by(name = user_id).first()
        if user:
            session.delete(user)
            session.commit()
            await message.answer(f'Менеджер успешно удален')
        else:
            await message.answer('Менеджера с таким ID не существует')
    except IndexError:
        await message.answer('Неправильное количество аргументов')


async def create_team_command(message: types.Message):
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


async def remove_team_command(message: types.Message):
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
    dp.register_message_handler(set_user, IsAdmin(), lambda m: m.text in ('Обновить баллы менеджера', 'Установить время перерыва', 'Установить рабочее время', 'Обновить роль', 'Удалить менеджера'), state = "*")
    dp.register_message_handler(set_score, IsAdmin(), state = Users.SET_SCORE)
    dp.register_message_handler(set_braketime, IsAdmin(), state = Users.SET_BRAKETIME)
    dp.register_message_handler(set_workday_range, IsAdmin(), state = Users.SET_WORKDAY)
    dp.register_message_handler(set_role, IsAdmin(), state = Users.SET_ROLE)
    dp.register_message_handler(handle_user_option, IsAdmin(), lambda m: m.text in ('Статистика', 'Создать команду', 'Удалить команду', 'Отправить сообщение в чаты', 'Создать менеджера'), state = "*")
    dp.register_message_handler(create_team, IsAdmin(), state = Users.ADD_TEAM)
    dp.register_message_handler(remove_team, IsAdmin(), state = Users.REMOVE_TEAM)
    dp.register_message_handler(send_message_to_department, IsAdmin(), state = Users.CHAT_MESSAGE)
    dp.register_message_handler(procces_action_with_user, IsAdmin(), state = Users.SET_USER)
    
    dp.register_message_handler(create_manager, IsAdmin(), commands = ['create_manager'])
    dp.register_message_handler(recive_manager_data, IsAdmin(), lambda m: m.text in roles, state = CreateUser.USER_ROLE)
    dp.register_message_handler(set_manager_team, lambda m: m.text in [team.name for team in session.query(Team).all()], state = CreateUser.TEAM)
    dp.register_message_handler(procces_create_manager, IsAdmin(), state = CreateUser.MESSAGE)
    dp.register_message_handler(remove_manager_command, IsAdmin(), commands = ['remove_manager'])
    dp.register_message_handler(update_manager_score_command, IsAdmin(), commands = ['update_manager_score'])
    dp.register_message_handler(show_department_statistics, IsAdmin(), commands = ['stats'])
    dp.register_message_handler(set_braketime, IsAdmin(), commands = ['set_braketime'])
    dp.register_message_handler(set_workday_range_command, IsAdmin(), commands = ['set_workday_range'])
    dp.register_message_handler(update_user_role, IsAdmin(), commands = ['update_role'])
    dp.register_message_handler(create_team_command, IsAdmin(), commands = ['create_team'])
    dp.register_message_handler(remove_team_command, IsAdmin(), commands = ['remove_team'])
    dp.register_message_handler(send_message_to_department, IsAdmin(), commands = ['send_message_to_chats']) 