from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, Update
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.repositories.admin_repo import AdminRepository
from database.repositories.shop_repo import ShopRepository
from database.repositories.user_repo import UserRepository


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        actual_event = event.event if isinstance(event, Update) else event
        tg_user = None
        if isinstance(actual_event, (Message, CallbackQuery)):
            if actual_event.from_user:
                tg_user = actual_event.from_user

        async with self.session_pool() as session:
            data["session"] = session

            admin_repo = AdminRepository(session)
            user_repo = UserRepository(session)
            shop_repo = ShopRepository(session)

            data["admin_repo"] = admin_repo
            data["user_repo"] = user_repo
            data["shop_repo"] = shop_repo

            db_user = None
            if tg_user:
                db_user = await user_repo.get_or_create_user(tg_user)

            data["user"] = db_user

            try:
                return await handler(event, data)
            except Exception:
                await session.rollback()
                raise

