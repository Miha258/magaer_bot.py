import asyncio
from datetime import datetime
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import *
from db import User, Chat, session, WeeklyStats, DailyStats

class CheckManagerDelay(StatesGroup):
    AWAITING_REPLY = State()

timeouts = {}
last_messages = {}

async def send_message_with_delay(chat_id: int, message: str):
    try:
        await bot.send_message(chat_id, message)
    except Exception as e:
        print(f"Error sending message to chat {chat_id}: {e}")


async def notify_admins(text: str, message_link: str):
    for admin in admins:
        try:
            await bot.send_message(admin, text, reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[[
                types.InlineKeyboardButton('Перейти в чат', url = message_link)
            ]]))
        except Exception as e:
            print(e)
            


chats = []
async def check_manager_delay(message: types.Message):
    if message.chat.full_name not in chats:
        chats.append(message.chat.full_name)
    print(chats)
    week_day = datetime.today().weekday()
    if week_day != 5 and week_day != 6:
        user_id = message.from_id
        user = session.query(User).filter_by(id = user_id).first()
        chat = session.query(Chat).filter_by(chat_id = message.chat.id).first()
        if message.text:
            last_message: types.Message = last_messages.get(message.chat.id)
            if not last_message:
                last_messages[message.chat.id] = message
                last_message = message
            elif last_message.message_id != message.message_id:
                last_messages[message.chat.id] = message
            if not user and chat:
                if '?' in message.text:
                    await asyncio.sleep(1800)
                    user = session.query(User).filter_by(id = message.from_id).first()
                    if not user:
                        if last_messages.get(message.chat.id).message_id == message.message_id:
                            manager = None
                            for m in session.query(User).filter_by(team_id = chat.team_id, role = 'Афф-менеджер').all():
                                user = await bot.get_chat_member(message.chat.id, m.id)
                                if user:
                                    if user.status != "kicked" and user.status != "left" and user.status != "banned":
                                        manager = m
                            if manager:
                                now = datetime.now()
                                if manager.paused < now and manager.end_work_at > now.time() and manager.start_work_at < now.time():
                                    tag_msg = await message.reply(f"Из-за высокой загруженности время ответа менеджера увеличивается, просим немного Вашего терпения! {manager.name}")
                                    await remove_score(manager.id, 1)
                                    await notify_admins(f'🛎 Тегнул {manager.name} в канале {message.chat.full_name} 🛎', tag_msg.url)
                            await asyncio.sleep(3600)
                            user = session.query(User).filter_by(id = message.from_id).first()
                            if not user:
                                if last_messages.get(message.chat.id).message_id == message.message_id:
                                    team_lead = session.query(User).filter_by(team_id = chat.team_id, role = 'Тимлид').first()
                                    now = datetime.now()
                                    if manager:
                                        if manager.paused < now or team_lead.paused < now:
                                            if manager.end_work_at > now.time() and manager.start_work_at < now.time() \
                                                and team_lead.end_work_at > now.time() and team_lead.start_work_at < now.time():
                                                tag_msg = await message.reply(f"Приносим извинения за задержку, скоро будет ответ {team_lead.name} {manager.name}")
                                                await notify_admins(f'🛎 Тегнул {team_lead.name} {manager.name} в канале {message.chat.full_name} 🛎', tag_msg.url)
                                                await remove_score(manager.id, 1)
                                    else:
                                        if team_lead.paused < now:
                                            if team_lead.end_work_at > now.time() and team_lead.start_work_at < now.time():
                                                tag_msg = await message.reply(f"Приносим извинения за задержку, скоро будет ответ {team_lead.name}")
                                                await notify_admins(f'🛎 Тегнул {team_lead.name} в канале {message.chat.full_name} 🛎', tag_msg.url)
                                    await asyncio.sleep(3600)
                                    user = session.query(User).filter_by(id = message.from_id).first()
                                    if not user:
                                        if last_messages.get(message.chat.id).message_id == message.message_id:
                                            now = datetime.now()
                                            if manager:
                                                if manager.paused < now:
                                                    await remove_score(manager.id, 5)
                                            if team_lead.paused < now:
                                                await remove_score(team_lead.id, 3)

                                            if manager:
                                                if team_lead.paused < now and manager.paused < now:
                                                    if manager.end_work_at > now.time() and manager.start_work_at < now.time() \
                                                        and team_lead.end_work_at > now.time() and team_lead.start_work_at < now.time():
                                                        await message.reply(f"Приносим извинения за задержку {team_lead.name} {manager.name} {head}")
                                                        await notify_admins(f'🛑 Тегнул {team_lead.name} {manager.name} {head} в канале {message.chat.full_name} 🛑', await message.chat.get_url())
                                            else:
                                                if team_lead.paused < now:
                                                    if team_lead.end_work_at > now.time() and team_lead.start_work_at < now.time():
                                                        await message.reply(f"Приносим извинения за задержку {team_lead.name} {head}")
                                                        await notify_admins(f'🛑 Тегнул {team_lead.name} {head} в канале {message.chat.full_name} 🛑', await message.chat.get_url())
            elif user and chat:
                if last_message:
                    if not session.query(User).filter_by(id = last_message.from_id).first() and '?' in last_message.text and user.role in ('Тимлид', 'Афф-менеджер'):
                        print('calculated')
                        calculate_average_reply_time(last_message, message)

async def remove_score(user_id: int, score: int):
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        WeeklyStats.update(user_id, quality_score = -score)
        DailyStats.update(user_id, quality_score = -score)
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
                DailyStats.update(user_id, average_reply_worktime = reply_time)
            else:
                user.average_reply_worktime = reply_time
                WeeklyStats.update(user_id, average_reply_worktime = reply_time)
                DailyStats.update(user_id, average_reply_worktime = reply_time)
        else:
            if user.average_reply_time:
                user.average_reply_time = (user.average_reply_time + reply_time) / 2
                WeeklyStats.update(user_id, average_reply_time = reply_time)
                DailyStats.update(user_id, average_reply_time = reply_time)
            else:
                user.average_reply_time = reply_time
                WeeklyStats.update(user_id, average_reply_time = reply_time)
                DailyStats.update(user_id, average_reply_time = reply_time)
        session.commit()



def register_tracker(dp: Dispatcher):
    dp.register_message_handler(check_manager_delay, lambda m: m is not None and m.chat.type in ('group', 'supergroup', 'channel'), content_types = [types.ContentType.TEXT, types.ContentType.VIDEO, types.ContentType.PHOTO, types.ContentType.ANIMATION, types.ContentType.DOCUMENT, types.ContentType.AUDIO], state="*")