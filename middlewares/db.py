from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.repositories.admin_repo import AdminRepository
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
        async with self.session_pool() as session:
            # 1. Добавляем саму сессию на случай непредвиденных ручных запросов
            data["session"] = session

            # 2. Инициализируем репозитории
            data["admin_repo"] = AdminRepository(session)
            data["user_repo"] = UserRepository(session)

            try:
                # Запускаем цепочку хэндлеров
                return await handler(event, data)
            except Exception:
                # 3. Безопасность: если хэндлер упал, принудительно откатываем
                # любые незакоммиченные изменения в этой сессии перед её закрытием
                await session.rollback()
                raise  # Пробрасываем ошибку дальше, чтобы её поймал диспетчер/логи