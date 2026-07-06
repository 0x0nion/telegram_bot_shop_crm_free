from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Русский 🇷🇺", callback_data="lang_ru")
    builder.button(text="English 🇺🇸", callback_data="lang_en")
    builder.adjust(2)
    return builder.as_markup()

def get_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Редактировать Магазин", callback_data="admin_shop")
    builder.button(text="Склад", callback_data="admin_warehouse")
    builder.button(text="👥 Юзеры", callback_data="admin_users")
    builder.button(text="Работники", callback_data="admin_workers")
    builder.button(text="Рассылка", callback_data="admin_alert")
    builder.button(text="Статистика", callback_data="admin_stat")
    builder.adjust(1,)
    return builder.as_markup()