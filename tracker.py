import asyncio
from datetime import datetime
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import *
from db import User, Chat, session, WeeklyStats, DailyStats, Tickets
import re


class CheckManagerDelay(StatesGroup):
    AWAITING_REPLY = State()

timeouts = {}
last_messages = {}

async def send_message_with_delay(chat_id: int, message: str):
    try:
        await bot.send_message(chat_id, message)
    except Exception as e:
        print(f"Error sending message to chat {chat_id}: {e}")


async def notify_admins(text: str, message_link: str, ticket_id: int = None):
    if ticket_id:
        for admin in admin_ids:
            try:
                await bot.send_message(admin, text, reply_markup = types.InlineKeyboardMarkup(inline_keyboard=[[
                    types.InlineKeyboardButton('Перейти в чат', url = message_link),
                    types.InlineKeyboardButton('Отменить', callback_data = f'cancle_ticket_{ticket_id}')
                ]]))
            except Exception as e:
                print(e)

url_regex = r'\b(?:https?|ftp)://[\w-]+(?:\.[\w-]+)+[\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-]'  
async def cancle_ticket(callback_data: types.CallbackQuery):
    ticket_id = int(callback_data.data.split('_')[-1])
    ticket = session.query(Tickets).filter_by(id = ticket_id).first()
    user = session.query(User).filter_by(id = ticket.user_id).first()
    if not user:
        return await callback_data.message.answer('Менеджер не найден')
    if ticket:
        user.quality_score = user.quality_score + ticket.score
        session.delete(ticket)
        session.commit()

        DailyStats.update(ticket.user_id, quality_score = ticket.score)
        WeeklyStats.update(ticket.user_id, quality_score = ticket.score)

        await callback_data.message.answer('Тикет успешно обработан!')
        try:
            await bot.delete_message(ticket.chat_id, ticket.message_id)
        except Exception as e:
            await callback_data.message.answer(f'Но не удалось удалить сообщения: {e}')
    else:
        await callback_data.message.answer('Тикет уже был обработан')
    await callback_data.message.delete_reply_markup()

chats = []
async def check_manager_delay(message: types.Message):
    if message.chat.full_name not in chats:
        chats.append(message.chat.full_name)

    if message.chat.full_name != "Тест бота":
        return
    week_day = datetime.today().weekday()
    if week_day != 5 and week_day != 6:
        user_id = message.from_id
        user = session.query(User).filter_by(id = user_id).first()
        chat = session.query(Chat).filter_by(chat_id = message.chat.id).first()

        messgae_text = message.caption if message.caption else message.text
        last_message: types.Message = last_messages.get(message.chat.id)
        if not last_message:
            last_messages[message.chat.id] = message
            last_message = message
        elif last_message.message_id != message.message_id:
            last_messages[message.chat.id] = message
            
        if not user and chat and message.from_user.username not in admins and messgae_text:
            if '?' in messgae_text and not re.findall(url_regex, messgae_text):
                await asyncio.sleep(15)
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
                            now = message.date
                            if manager.paused > now:
                                return
                            if manager.start_work_at <= now.time() <= manager.end_work_at:
                                tag_msg = await message.reply(f"Из-за высокой загруженности время ответа менеджера увеличивается, просим немного Вашего терпения! {manager.name}")
                                ticket_id = await remove_score(manager.id, 1, tag_msg.message_id, message.chat.id)
                                await notify_admins(f'🛎 Тегнул {manager.name} в канале {message.chat.full_name} 🛎', await message.chat.get_url(), ticket_id)
                        await asyncio.sleep(15)
                        user = session.query(User).filter_by(id = message.from_id).first()
                        if not user:
                            if last_messages.get(message.chat.id).message_id == message.message_id:
                                team_lead = session.query(User).filter_by(team_id = chat.team_id, role = 'Тимлид').first()
                                now = message.date
                                if manager:
                                    if manager.paused > now:
                                        return
                                    if manager.start_work_at <= now.time() <= manager.end_work_at \
                                        and team_lead.start_work_at <= now.time() <= team_lead.end_work_at:
                                        tag_msg = await message.reply(f"Приносим извинения за задержку, скоро будет ответ {team_lead.name} {manager.name}")
                                        ticket_id = await remove_score(manager.id, 3, tag_msg.message_id, message.chat.id)
                                        await notify_admins(f'🛎 Тегнул {team_lead.name} {manager.name} в канале {message.chat.full_name} 🛎', await message.chat.get_url(), ticket_id)
                                else:
                                    if team_lead.paused > now:
                                        return
                                    if team_lead.start_work_at <= now.time() <= team_lead.end_work_at:
                                        tag_msg = await message.reply(f"Приносим извинения за задержку, скоро будет ответ {team_lead.name}")
                                        ticket_id = await remove_score(team_lead.id, 0, tag_msg.message_id, message.chat.id)
                                        await notify_admins(f'🛎 Тегнул {team_lead.name} в канале {message.chat.full_name} 🛎', await message.chat.get_url(), ticket_id)
                                await asyncio.sleep(15)
                                user = session.query(User).filter_by(id = message.from_id).first()
                                if not user:
                                    tag_msg = None
                                    if last_messages.get(message.chat.id).message_id == message.message_id:
                                        if manager and team_lead:
                                            if team_lead.paused > now and manager.paused < now:
                                                return
                                            if manager.start_work_at <= now.time() <= manager.end_work_at \
                                                and team_lead.start_work_at <= now.time() <= team_lead.end_work_at:
                                                tag_msg = await message.reply(f"Приносим извинения за задержку {team_lead.name} {manager.name} {head}")
                                        else:
                                            if team_lead.paused < now:
                                                return
                                            if team_lead.start_work_at <= now.time() <= team_lead.end_work_at:
                                                tag_msg = await message.reply(f"Приносим извинения за задержку {team_lead.name} {head}")
                                        
                                        now = message.date
                                        if manager:
                                            if manager.paused > now and manager.start_work_at <= now.time() <= manager.end_work_at:
                                                ticket_id = await remove_score(manager.id, 5, tag_msg.message_id, message.chat.id)
                                                await notify_admins(f'🛑 Тегнул {manager.name} в канале {message.chat.full_name} 🛑', await message.chat.get_url(), ticket_id)
                                        if team_lead.paused < now and team_lead.start_work_at <= now.time() <= team_lead.end_work_at:
                                            ticket_id = await remove_score(team_lead.id, 3, tag_msg.message_id, message.chat.id)
                                            await notify_admins(f'🛑 Тегнул {team_lead.name} {head} в канале {message.chat.full_name} 🛑', await message.chat.get_url(), ticket_id)
        elif user and chat:
            if last_message:
                if not session.query(User).filter_by(id = last_message.from_id).first() and '?' in last_message.text and user.role in ('Тимлид', 'Афф-менеджер'):
                    print('calculated')
                    calculate_average_reply_time(last_message, message)

async def remove_score(user_id: int, score: int, message_id: int, chat_id: int):
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        WeeklyStats.update(user_id, quality_score = -score)
        DailyStats.update(user_id, quality_score = -score)
        ticket_id = Tickets.create(user_id, score, message_id, chat_id)
        user.quality_score -= score
        session.commit()
        return ticket_id

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
    dp.register_callback_query_handler(cancle_ticket, lambda cb: "cancle_ticket" in cb.data)
    dp.register_message_handler(check_manager_delay, lambda m: m is not None and m.chat.type in ('group', 'supergroup', 'channel'), content_types = [types.ContentType.TEXT, types.ContentType.VIDEO, types.ContentType.PHOTO, types.ContentType.ANIMATION, types.ContentType.DOCUMENT, types.ContentType.VOICE, types.ContentType.AUDIO], state="*")