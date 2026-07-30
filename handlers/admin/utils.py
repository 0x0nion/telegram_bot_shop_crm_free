# handlers/admin/utils.py
import asyncio
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest
from database.models.user import User

SUPPORTED_LANGUAGES = {"ru", "en", "es"}
DEFAULT_LANGUAGE = "en"


def get_user_lang(user: User) -> str:
    """DRY: Безопасное определение языка пользователя."""
    if user and user.language in SUPPORTED_LANGUAGES:
        return user.language
    return DEFAULT_LANGUAGE


def parse_id(raw_value: str) -> int | None:
    """DRY: Преобразование строкового ID из callback_data (с учетом 'root')."""
    return int(raw_value) if raw_value and raw_value != "root" else None


async def self_destruct(message: Message, seconds: int = 3) -> None:
    """Автоматическое удаление служебного сообщения через заданное время."""
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass