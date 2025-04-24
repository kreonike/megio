import logging
from logging.config import dictConfig
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client import telegram
from aiogram import Bot, Dispatcher
import asyncio
from bot.handlers.commands import register_handlers as reg_commands
from bot.handlers.callbacks import register_handlers as reg_callbacks
from bot.handlers.messages import register_handlers as reg_messages
from bot.utils.reminders import check_reminders
from bot.config.logging_config import dict_config
import sys
from pathlib import Path
from bot.config.config import DB_PATH
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from bot.config.models import Base

load_dotenv()

project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

dictConfig(dict_config)
logger = logging.getLogger("bot")

async def init_db():
    logger.info("Начинаем инициализацию базы данных")
    try:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        Base.metadata.create_all(engine)
        logger.info("Таблицы базы данных успешно созданы/проверены")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = result.fetchall()
            logger.info(f"Таблицы в базе данных: {tables}")
    except SQLAlchemyError as e:
        logger.error(f"Ошибка инициализации базы данных: {e}", exc_info=True)
        raise

async def get_db_session():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Session = sessionmaker(bind=engine)
    return Session()

async def main():
    logger.info("Starting bot initialization")
    bot_token = os.getenv("BOT_TOKEN")
    api_base_url = os.getenv("API_BASE_URL")
    session = AiohttpSession(api=telegram.TelegramAPIServer.from_base(api_base_url))
    bot = Bot(token=bot_token, session=session)
    dp = Dispatcher()

    await init_db()
    reg_commands(dp)
    reg_callbacks(dp)
    reg_messages(dp)

    db_session = await get_db_session()
    logger.info("Starting bot with ORM database")
    await asyncio.gather(
        dp.start_polling(bot),
        check_reminders(bot=bot, session=db_session, interval=30)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Bot crashed: {e}", exc_info=True)