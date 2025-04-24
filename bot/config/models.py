from sqlalchemy import Column, Integer, String, Boolean, Time, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False)
    email = Column(String, nullable=False)

    telegram_account = relationship("TelegramUser", back_populates="user", uselist=False)
    tasks = relationship("Task", back_populates="user")

class TelegramUser(Base):
    __tablename__ = 'telegram_users'

    telegram_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship("User", back_populates="telegram_account")

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    task = Column(String, nullable=False)
    time = Column(Time)
    created = Column(DateTime, server_default='CURRENT_TIMESTAMP')
    reminder_1day_sent = Column(Boolean, default=False)
    reminder_2h_sent = Column(Boolean, default=False)
    reminder_15m_sent = Column(Boolean, default=False)

    user = relationship("User", back_populates="tasks")