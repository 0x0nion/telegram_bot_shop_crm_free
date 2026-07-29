import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database.models.user import User
from database.repositories.admin_repo import AdminRepository
from handlers.admin.show_admin_panel import show_admin_panel
from keyboards.admin_inline import AdminInlineKb

admin_main_router = Router()
logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"ru", "en", "es"}
DEFAULT_LANGUAGE = "en"


def _get_user_lang(user: User) -> str:
    """DRY: Безопасное определение языка пользователя."""
    if user and user.language in SUPPORTED_LANGUAGES:
        return user.language
    return DEFAULT_LANGUAGE


@admin_main_router.message(Command("admin"))
@admin_main_router.callback_query(F.data == "admin")
async def cmd_admin_entry(
        event: Message | CallbackQuery, admin_repo: AdminRepository, user: User
):
    """Единая точка входа в админ-панель (DRY)."""
    await show_admin_panel(event, admin_repo, user=user, sync=True)


@admin_main_router.callback_query(F.data == "admin_shop_settings")
async def cb_shop_settings(callback: CallbackQuery, user: User):
    """Открытие подменю 'Настройка магазина'."""
    lang = _get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    markup = kb.get_shop_settings_kb()
    title_text = kb.get_text("welcome_title", "🔑 Панель администратора открыта:")
    text = f"{title_text}\n\n⚙️ <b>Настройка магазина:</b>"

    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=markup, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

    await callback.answer()


@admin_main_router.callback_query(F.data == "admin_save_shop")
async def cb_admin_save(
        callback: CallbackQuery, admin_repo: AdminRepository, user: User
):
    await admin_repo.commit_changes(admin_id=callback.from_user.id)
    await show_admin_panel(
        callback, admin_repo, user=user, is_saved=True, sync=True
    )


@admin_main_router.callback_query(F.data == "admin_mainmenu")
async def back_to_main_menu(
        callback: CallbackQuery, admin_repo: AdminRepository, user: User
):
    await show_admin_panel(callback, admin_repo, user=user, sync=False)


@admin_main_router.callback_query(F.data.startswith("admin_"))
async def catch_other_admin_actions(callback: CallbackQuery, user: User):
    """Заглушка для нереализованных разделов админки."""
    parts = callback.data.split("_")
    # Для ключей вроде admin_warehouse берем parts[1], для двойных — можно адаптировать
    action = parts[1] if len(parts) > 1 else "default"

    lang = _get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    alert_message = kb.get_text(f"alerts.{action}") or kb.get_text(
        "alerts.default", "Раздел в разработке..."
    )

    await callback.answer(alert_message, show_alert=True)