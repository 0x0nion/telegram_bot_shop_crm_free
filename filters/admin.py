from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message
from config import config


class IsAdminFilter(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        # return event.from_user.id in config.ADMIN_ID
        return True

