from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
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
        # Извлекаем объект Telegram-пользователя (from_user есть и в Message, и в CallbackQuery)
        tg_user = None
        if isinstance(event, (Message, CallbackQuery)):
            tg_user = event.from_user

        async with self.session_pool() as session:
            # 1. Добавляем саму сессию в контекст
            data["session"] = session

            # 2. Инициализируем репозитории
            admin_repo = AdminRepository(session)
            user_repo = UserRepository(session)
            shop_repo = ShopRepository(session)

            data["admin_repo"] = admin_repo
            data["user_repo"] = user_repo
            data["shop_repo"] = shop_repo

            # 3. Получаем или создаем пользователя БД и прокидываем его в хендлеры
            db_user = None
            if tg_user:
                db_user = await user_repo.get_or_create_user(tg_user)

            data["user"] = db_user  # Теперь во всех хендлерах доступен аргумент `user: User`

            try:
                # Запускаем цепочку хэндлеров
                return await handler(event, data)
            except Exception:
                # Безопасность: принудительный откат при любой ошибке
                await session.rollback()
                raise
            finally:
                # Гарантированное закрытие сессии
                await session.close()