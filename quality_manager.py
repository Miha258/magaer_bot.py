from aiogram import types
from sqlalchemy import func
from config import *
from utils import *
from db import session, User, WeeklyStats, DailyStats
from keyboards import *

async def show_department_statistics(message: types.Message):
    response = "Статистика отдела:\n"
    members = session.query(User).all()
    for member in members:
        avrg_worktime = f"{int((member.average_reply_worktime / 60) // 60)} час. {int((member.average_reply_worktime / 60) % 60)} мин." if member.average_reply_worktime else "0 час. 0 мин." 
        avrg_time = f"{int((member.average_reply_time / 60) // 60)} час. {int((member.average_reply_time / 60) % 60)} мин." if member.average_reply_time else "0 час. 0 мин."
        braketime = ", <strong>Перерыв до: </strong>" + datetime.strftime(member.paused, "%Y.%m.%d-%H:%M") if member.paused > datetime.now() else ""
        response += f"{member.name}, <strong>Роль:</strong> {member.role}, <strong>ID:</strong> {member.id}, <strong>Баллы</strong>: {member.quality_score}, <strong>Команда:</strong> {'нет' if not member.team_id else member.team_id}, <strong>Рабочее время:</strong> {':'.join(str(member.start_work_at).split(':')[:-1])}-{':'.join(str(member.end_work_at).split(':')[:-1])}, <strong>Среднее время ответа в рабочее время:</strong> {avrg_worktime}, <strong>Среднее время ответа в нерабочее время:</strong> {avrg_time} {braketime}\n\n"
    await message.answer(response, parse_mode = 'html')
    

async def show_department_statistics_weekly(message: types.Message):
    response = "Статистика отдела за неделю:\n"
    now = datetime.now()
    members = session.query(WeeklyStats).filter(
        WeeklyStats.start_day < now,
        WeeklyStats.end_day > now
    ).order_by(WeeklyStats.quality_score).all()
    for member in members:
        user = session.query(User).filter_by(id = member.user_id).first()
        avrg_worktime = f"{int((member.average_reply_worktime / 60) // 60)} час. {int((member.average_reply_worktime / 60) % 60)} мин." if member.average_reply_worktime else "0 час. 0 мин." 
        avrg_time = f"{int((member.average_reply_time / 60) // 60)} час. {int((member.average_reply_time / 60) % 60)} мин." if member.average_reply_time else "0 час. 0 мин."
        if user:
            braketime = ", <strong>Перерыв до: </strong>" + datetime.strftime(user.paused, "%Y.%m.%d-%H:%M") if user.paused > datetime.now() else ""
            response += f"{user.name}, <strong>Роль:</strong> {user.role}, <strong>ID:</strong> {user.id}, <strong>Баллы</strong>: {member.quality_score}, <strong>Команда:</strong> {'нет' if not user.team_id else user.team_id}, <strong>Рабочее время:</strong> {':'.join(str(user.start_work_at).split(':')[:-1])}-{':'.join(str(user.end_work_at).split(':')[:-1])}, <strong>Среднее время ответа в рабочее время:</strong> {avrg_worktime}, <strong>Среднее время ответа в нерабочее время:</strong> {avrg_time} {braketime}\n\n"
    await message.answer(response, parse_mode = 'html')

async def show_department_statistics_daily(message: types.Message):
    response = "Статистика отдела за день:\n"
    members = session.query(DailyStats).filter(
        func.date(DailyStats.date) == datetime.today().date()
    ).order_by(DailyStats.quality_score).all()
    for member in members:
        user = session.query(User).filter_by(id = member.user_id).first()
        avrg_worktime = f"{int((member.average_reply_worktime / 60) // 60)} час. {int((member.average_reply_worktime / 60) % 60)} мин." if member.average_reply_worktime else "0 час. 0 мин." 
        avrg_time = f"{int((member.average_reply_time / 60) // 60)} час. {int((member.average_reply_time / 60) % 60)} мин." if member.average_reply_time else "0 час. 0 мин."
        if user:
            braketime = ", <strong>Перерыв до: </strong>" + datetime.strftime(user.paused, "%Y.%m.%d-%H:%M") if user.paused > datetime.now() else ""
            response += f"{user.name}, <strong>Роль:</strong> {user.role}, <strong>ID:</strong> {user.id}, <strong>Баллы</strong>: {member.quality_score}, <strong>Команда:</strong> {'нет' if not user.team_id else user.team_id}, <strong>Рабочее время:</strong> {':'.join(str(user.start_work_at).split(':')[:-1])}-{':'.join(str(user.end_work_at).split(':')[:-1])}, <strong>Среднее время ответа в рабочее время:</strong> {avrg_worktime}, <strong>Среднее время ответа в нерабочее время:</strong> {avrg_time} {braketime}\n\n"
    await message.answer(response, parse_mode = 'html')


def register_quality_manager(dp: Dispatcher):
    dp.register_message_handler(show_department_statistics, IsQualityManager(), commands=['stats'])
    dp.register_message_handler(show_department_statistics_weekly, IsQualityManager(), commands=['weekly_stats'])
    dp.register_message_handler(show_department_statistics, IsQualityManager(), commands=['monthly_stats'])
    dp.register_message_handler(show_department_statistics_daily, IsQualityManager(), commands=['daily_stats'])