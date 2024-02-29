import asyncio
from datetime import datetime
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import *
from db import User, Chat, session, WeeklyStats, MonthlyStats

class CheckManagerDelay(StatesGroup):
    AWAITING_REPLY = State()

timeouts = {}
last_message = None


async def send_message_with_delay(chat_id: int, message: str):
    try:
        await bot.send_message(chat_id, message)
    except Exception as e:
        print(f"Error sending message to chat {chat_id}: {e}")

async def check_manager_delay(message: types.Message):
    global last_message
    last_message = message
   
    user_id = message.from_user.id
    user = session.query(User).filter_by(id = user_id).first()
    chat = session.query(Chat).filter_by(chat_id = message.chat.shifted_id).first()
    if not user and chat:
        await asyncio.sleep(10)
        if last_message.message_id == message.message_id:
            manager = session.query(User).filter_by(team_id = chat.team_id, role = 'Афф-менеджер').first()
            await last_message.reply(f"Из-за высокой загруженности время ответа менеджера увеличивается, просим немного Вашего терпения! {manager.name}")
            if manager.paused < datetime.now():
                await remove_score(manager.id, 1)
            await asyncio.sleep(10)
            if last_message.message_id == message.message_id:
                team_lead = session.query(User).filter_by(team_id = manager.team_id, role = 'Тимлид').first()
                await last_message.reply(f"Приносим извинения за задержку, скоро будет ответ {team_lead.name} {manager.name}")
                if manager.paused < datetime.now():
                    await remove_score(manager.id, 1)
                await asyncio.sleep(10)
                if last_message.message_id == message.message_id:
                    if manager.paused < datetime.now():
                        await remove_score(manager.id, 5)
                    if team_lead.paused < datetime.now():
                        await remove_score(team_lead.id, 3)
                    await last_message.reply(f"Приносим извинения за задержку {team_lead.name} {manager.name} {head}")

async def remove_score(user_id: int, score: int):
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        user.quality_score -= score
        session.commit()

def calculate_average_reply_time(message: types.Message):
    user_id = message.from_user.id
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        reply_time = message.date - message.reply_to_message.date
        start_work_time = user.start_work_at
        end_work_time = user.end_work_at
        if start_work_time <= message.date.time() <= end_work_time:
            if user.average_reply_worktime:
                user.average_reply_worktime = (user.average_reply_worktime + reply_time.total_seconds() / 60) / 2
            else:
                user.average_reply_worktime = reply_time.total_seconds() / 60
        else:
            if user.average_reply_time:
                user.average_reply_time = (user.average_reply_time + reply_time.total_seconds() / 60) / 2
            else:
                user.average_reply_time = reply_time.total_seconds() / 60
        session.commit()
        WeeklyStats.update(session, user_id)
        MonthlyStats.update(session, user_id)



def register_tracker(dp: Dispatcher):
    dp.register_message_handler(check_manager_delay, lambda m: m is not None and m.text.endswith('?') and m.chat.type in ('group', 'supergroup'), content_types = types.ContentTypes.TEXT | types.ContentTypes.PHOTO | types.ContentTypes.VIDEO, state="*")
    dp.register_message_handler(calculate_average_reply_time, lambda m: m.reply_to_message is not None, content_types = types.ContentType.ANY, state="*")