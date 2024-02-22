from aiogram import types
from config import *
from utils import *
from db import session, User


async def show_department_statistics(message: types.Message):
    response = "Статистика отдела:\n"
    members = session.query(User).filter_by()
    for member in members:
        avrg_worktime = member.average_reply_worktime / 60 if member.average_reply_worktime else 0 
        avrg_time = member.average_reply_time / 60 if member.average_reply_time else 0
        braketime = ", <strong>Прерван до: </strong>" + datetime.strftime(member.paused, "%Y.%m.%d-%H:%M") if member.paused > datetime.now() else ""
        response += f"{member.name}, <strong>Роль:</strong> {member.role}, <strong>ID:</strong> {member.id}, <strong>Баллы</strong>: {member.quality_score}, <strong>Команда:</strong> {'нет' if not member.team_id else member.team_id}, <strong>Рабочее время:</strong> {':'.join(str(member.start_work_at).split(':')[:-1])}-{':'.join(str(member.end_work_at).split(':')[:-1])}, <strong>Сред.Рабочее:</strong> {avrg_worktime:.2f}мин, <strong>Сред.Нерабочее:</strong> {avrg_time:.2f}мин{braketime}\n\n"
    await message.answer(response, parse_mode = 'html')


def register_quality_manager(dp: Dispatcher):
    dp.register_message_handler(show_department_statistics, IsQualityManager(), commands=['stats'])