from sqlalchemy import create_engine, Column, Integer, String, DateTime, Time, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, time, timedelta

DATABASE_URL = 'sqlite:///bots.db'
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    role = Column(String)
    quality_score = Column(Integer, default=100)
    team_id = Column(Integer, nullable=True)
    paused = Column(DateTime, default=datetime.now())
    start_work_at = Column(Time, default=time(0, 0))
    end_work_at = Column(Time, default=time(23, 0))
    average_reply_time = Column(Integer, default=0)
    average_reply_worktime = Column(Integer, default=0)

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    teamlead_id = Column(Integer, nullable=True)
    name = Column(String)

class Chat(Base):
    __tablename__ = 'chats'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, unique=True)
    team_id = Column(Integer)

class WeeklyStats(Base):
    __tablename__ = 'weekly_stats'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    quality_score = Column(Integer, default=100)
    average_reply_time = Column(Integer, default=0)
    average_reply_worktime = Column(Integer, default=0)
    start_day = Column(DateTime)  
    end_day = Column(DateTime)

    @classmethod
    def update(cls, user_id, quality_score=None, average_reply_time=None, average_reply_worktime=None):
        current_time = datetime.now()
        weekly_stats = None
        for stats in session.query(cls).filter_by(user_id = user_id).all():
            if stats.start_day < current_time and stats.end_day > current_time:
                weekly_stats = stats
                break
        
        if weekly_stats:
            if quality_score:
                weekly_stats.quality_score = weekly_stats.quality_score + quality_score
            if average_reply_time:
                weekly_stats.average_reply_time = weekly_stats.average_reply_time + average_reply_time
            if average_reply_worktime:
                weekly_stats.average_reply_worktime = weekly_stats.average_reply_worktime + average_reply_worktime
        else:
            start_of_week = current_time - timedelta(days = current_time.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            weekly_stats = cls(user_id=user_id, quality_score=quality_score, average_reply_time=average_reply_time, average_reply_worktime=average_reply_worktime, start_day=start_of_week, end_day=end_of_week)
            session.add(weekly_stats)
        session.commit()

class DailyStats(Base):
    __tablename__ = 'daily_stats'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    quality_score = Column(Integer, default=100)
    average_reply_time = Column(Integer, default=0)
    average_reply_worktime = Column(Integer, default=0)
    date = Column(DateTime)

    @classmethod
    def update(cls, user_id, quality_score=None, average_reply_time=None, average_reply_worktime=None):
        current_time = datetime.today().date()
        daily_stats = None
        for stats in session.query(cls).filter_by(user_id = user_id).all():
            if stats.date.date() == current_time:
                daily_stats = stats
                break

        if daily_stats:
            if quality_score:
                daily_stats.quality_score += quality_score
            if average_reply_time:
                daily_stats.average_reply_time += average_reply_time
            if average_reply_worktime:
                daily_stats.average_reply_worktime += average_reply_worktime
        else:
            daily_stats = cls(date = datetime.today(), user_id=user_id, quality_score=quality_score, average_reply_time=average_reply_time, average_reply_worktime=average_reply_worktime)
            session.add(daily_stats)

        session.commit()

class MonthlyStats(Base):
    __tablename__ = 'monthly_stats'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    quality_score = Column(Integer, default=100)
    average_reply_time = Column(Integer, default=0)
    average_reply_worktime = Column(Integer, default=0)

metadata = MetaData()

def create_tables():
    Base.metadata.create_all(bind=engine)

Session = sessionmaker(engine)
session = Session()
create_tables()
session.commit()
