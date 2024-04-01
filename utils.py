from datetime import datetime
from aiogram import types
from config import admins
from db import session, User
from aiogram.dispatcher.filters import BoundFilter


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y.%m.%d-%H:%M")
        return datetime.strptime(date_str, "%Y.%m.%d-%H:%M")
    except ValueError:
        return None
    

def is_valid_time(time_str):
    try:
        datetime.strptime(time_str, "%H:%M")
        return datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return None
    
class IsAffManager(BoundFilter):
    key = 'is_aff_manager'
    async def check(self, message: types.Message) -> bool:
        user_id = message.from_user.id
        user = session.query(User).filter_by(id=user_id).first()
        if user and user.role == 'Афф-менеджер':
            return True
        return False
    

class IsQualityManager(BoundFilter):
    key = 'is_quality_manager'
    async def check(self, message: types.Message) -> bool:
        user_id = message.from_user.id
        user = session.query(User).filter_by(id=user_id).first()

        if user and user.role == 'Кволити-менеджер':
            return True
        return False
    

class IsTeamlead(BoundFilter):
    key = 'is_team_lead'

    async def check(self, message: types.Message) -> bool:
        user_id = message.from_user.id
        user = session.query(User).filter_by(id=user_id).first()
        if user and user.role == 'Тимлид':
            return True
        return False
    
class IsAdmin(BoundFilter):
    key = 'is_admin'
    
    async def check(self, message: types.Message) -> bool:
        user_id = message.from_user.username
        return user_id in admins