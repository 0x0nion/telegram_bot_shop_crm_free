import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import config
from database.connection import async_session, init_db

from handlers.admin import admin_group_router
from handlers.user import user_router
from middlewares.db import DbSessionMiddleware
from aiogram.fsm.storage.memory import MemoryStorage


async def main():
    logging.basicConfig(level=logging.INFO)

    await init_db()

    bot = Bot(
        token=config.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(
        storage=MemoryStorage()
    )

    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))

    dp.include_routers(admin_group_router, user_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())