from aiogram import types
from config import *
from utils import *
from db import session, User
from datetime import time

async def show_personal_statistics(message: types.Message):
    user_id = message.from_user.id
    user = session.query(User).filter_by(id = user_id).first()
    if user:
        avrg_worktime = user.average_reply_worktime / 60 if user.average_reply_worktime else 0 
        avrg_time = user.average_reply_time / 60 if user.average_reply_time else 0
        response = f"<strong>Личная статистика:</strong>\n\n"
        response += f"<strong>Количество баллов:</strong> {user.quality_score}\n"
        response += f"<strong>Начало рабочего времени:</strong> {':'.join(str(user.start_work_at).split(':')[:-1])}\n"
        response += f"<strong>Конец рабочего времени:</strong> {':'.join(str(user.end_work_at).split(':')[:-1])}\n"
        response += f"<strong>Среднее время ответа в рабочее время:</strong> {avrg_worktime:.2f} мин.\n"
        response += f"<strong>Среднее время ответа в нерабочее время:</strong> {avrg_time:.2f} мин.\n"
        await message.answer(response, parse_mode='html')
    else:
        await message.answer("Вы не зарегистрированы в системе.")

def register_aff_manager(dp: Dispatcher):
    dp.register_message_handler(show_personal_statistics, IsAffManager(), commands=['personal_stats'])