import asyncio
from datetime import datetime
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import *
from db import User, Chat, session, WeeklyStats, MonthlyStats

class CheckManagerDelay(StatesGroup):
    AWAITING_REPLY = State()

timeouts = {}
last_messages = {}


async def send_message_with_delay(chat_id: int, message: str):
    try:
        await bot.send_message(chat_id, message)
    except Exception as e:
        print(f"Error sending message to chat {chat_id}: {e}")

async def check_manager_delay(message: types.Message):
    week_day = datetime.today().weekday()
    if week_day != 5 and week_day != 6:
        last_message: types.Message = last_messages.get(message.chat.id)
        if not last_message:
            last_messages[message.chat.id] = message
            last_message = message
        elif last_message.message_id != message.message_id:
            last_messages[message.chat.id] = message

        user_id = message.from_user.id
        user = session.query(User).filter_by(id = user_id).first()
        chat = session.query(Chat).filter_by(chat_id = message.chat.id).first()
        if message.text:
            if not user and chat:
                if '?' in last_message.text:
                    print('waiting')
                    await asyncio.sleep(1800)
                    if last_messages.get(message.chat.id).message_id == message.message_id:
                        manager = None
                        for m in session.query(User).filter_by(team_id = chat.team_id, role = 'Афф-менеджер').all():
                            user = await bot.get_chat_member(message.chat.id, m.id)
                            if user:
                                if user.status != "kicked" and user.status != "left" and user.status != "banned":
                                    manager = m
                        if manager:
                            if manager.paused < datetime.now() and manager.end_work_at > datetime.now().time() and manager.start_work_at < datetime.now().time():
                                await last_message.reply(f"Из-за высокой загруженности время ответа менеджера увеличивается, просим немного Вашего терпения! {manager.name}")
                                await remove_score(manager.id, 1)
                        await asyncio.sleep(3600)
                        if last_messages.get(message.chat.id).message_id == message.message_id:
                            team_lead = session.query(User).filter_by(team_id = chat.team_id, role = 'Тимлид').first()
                            if manager:
                                if manager.paused < datetime.now() or team_lead.paused < datetime.now():
                                    if manager.end_work_at > datetime.now().time() and manager.start_work_at < datetime.now().time() \
                                        and team_lead.end_work_at > datetime.now().time() and team_lead.start_work_at < datetime.now().time():
                                        await last_message.reply(f"Приносим извинения за задержку, скоро будет ответ {team_lead.name} {manager.name}")
                                        await remove_score(manager.id, 1)
                            else:
                                if team_lead.paused < datetime.now():
                                    if team_lead.end_work_at > datetime.now().time() and team_lead.start_work_at < datetime.now().time():
                                        await last_message.reply(f"Приносим извинения за задержку, скоро будет ответ {team_lead.name}")
                            await asyncio.sleep(3600)
                            if last_messages.get(message.chat.id).message_id == message.message_id:
                                if manager:
                                    if manager.paused < datetime.now():
                                        await remove_score(manager.id, 5)
                                if team_lead.paused < datetime.now():
                                    await remove_score(team_lead.id, 3)

                                if manager:
                                    if team_lead.paused < datetime.now() and manager.paused < datetime.now():
                                        if manager.end_work_at > datetime.now().time() and manager.start_work_at < datetime.now().time() \
                                            and team_lead.end_work_at > datetime.now().time() and team_lead.start_work_at < datetime.now().time():
                                            await last_message.reply(f"Приносим извинения за задержку {team_lead.name} {manager.name} {head}")
                                else:
                                    if team_lead.paused < datetime.now():
                                        if team_lead.end_work_at > datetime.now().time() and team_lead.start_work_at < datetime.now().time():
                                            await last_message.reply(f"Приносим извинения за задержку {team_lead.name} {head}")
                        
            elif user and chat:
                if not session.query(User).filter_by(id = last_message.from_id).first() and '?' in last_message.text:
                    print('calculated')
                    calculate_average_reply_time(last_message, message)

async def remove_score(user_id: int, score: int):
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        WeeklyStats.update(user_id, quality_score = user.quality_score - score)
        user.quality_score -= score
        session.commit()

def calculate_average_reply_time(message: types.Message, reply_to_message: types.Message):
    user_id = reply_to_message.from_user.id
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        reply_time = (reply_to_message.date - message.date).total_seconds()
        start_work_time = user.start_work_at
        end_work_time = user.end_work_at
        if start_work_time <= message.date.time() <= end_work_time:
            if user.average_reply_worktime:
                user.average_reply_worktime = (user.average_reply_worktime + reply_time) / 2
                WeeklyStats.update(user_id, average_reply_worktime = reply_time)
            else:
                user.average_reply_worktime = reply_time
                WeeklyStats.update(user_id, average_reply_worktime = reply_time)
        else:
            if user.average_reply_time:
                user.average_reply_time = (user.average_reply_time + reply_time) / 2
                WeeklyStats.update(user_id, average_reply_time = (user.average_reply_time + reply_time) / 2)
            else:
                user.average_reply_time = reply_time
                WeeklyStats.update(user_id, average_reply_time = reply_time)
        session.commit()



def register_tracker(dp: Dispatcher):
    dp.register_message_handler(check_manager_delay, lambda m: m is not None and m.chat.type in ('group', 'supergroup'), content_types = types.ContentTypes.TEXT | types.ContentTypes.PHOTO | types.ContentTypes.VIDEO, state="*")