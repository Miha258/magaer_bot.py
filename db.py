from sqlalchemy import create_engine, Time, Column, Integer, String, DateTime, MetaData 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, time


DATABASE_URL = 'sqlite:///bots.db'
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)  # Добавьте primary_key=True
    name = Column(String)
    role = Column(String)
    quality_score = Column(Integer, default=100)
    team_id = Column(Integer, nullable=True)
    paused = Column(DateTime, default = datetime.now())
    start_work_at = Column(Time, default = time(0, 0))
    end_work_at = Column(Time, default = time(23, 0))
    average_reply_time = Column(Integer, default = 0)
    average_reply_worktime = Column(Integer, default = 0)


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

metadata = MetaData()
def create_tables():
    Base.metadata.create_all(bind=engine)

Session = sessionmaker(engine)
session = Session()