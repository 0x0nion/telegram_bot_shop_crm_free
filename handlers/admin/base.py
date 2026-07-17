import logging
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database.repositories.admin_repo import AdminRepository
from keyboards.admin_inline import AdminInlineKb
from database.models.user import User

admin_base_router = Router()
logger = logging.getLogger(__name__)


# --- Вспомогательная функция для отображения меню ---
async def show_admin_panel(
    event: Message | CallbackQuery,
    admin_repo: AdminRepository,
    user: User,
    is_saved: bool = False,
    sync: bool = False
):
    """
    Единая точка входа для отображения админ-панели.
    """
    if sync:
        await admin_repo.sync_to_temp(admin_id=event.from_user.id)

    # Всегда берем из user.language
    lang = user.language if user.language in ["ru", "en", "es"] else "en"
    kb = AdminInlineKb(lang=lang)

    text = kb.get_text("welcome_title", "🔑 Панель администратора открыта:")
    if is_saved:
        text += kb.get_text("shop_updated", "\n\n✅ Магазин обновлен!")

    reply_markup = kb.get_kb("admin_main_menu")

    try:
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=reply_markup)
            await event.answer()
        else:
            await event.answer(text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            if isinstance(event, CallbackQuery):
                await event.answer()
        else:
            raise e


@admin_base_router.message(Command("admin"))
async def cmd_admin(message: Message, admin_repo: AdminRepository, user: User):
    await show_admin_panel(message, admin_repo, user=user, sync=True)


@admin_base_router.callback_query(F.data == 'admin')
async def cb_admin(callback: CallbackQuery, admin_repo: AdminRepository, user: User):
    await show_admin_panel(callback, admin_repo, user=user, sync=True)


@admin_base_router.callback_query(F.data == 'admin_save_shop')
async def cb_admin_save(callback: CallbackQuery, admin_repo: AdminRepository, user: User):
    await admin_repo.commit_changes(admin_id=callback.from_user.id)
    await show_admin_panel(callback, admin_repo, user=user, is_saved=True, sync=True)


@admin_base_router.callback_query(F.data == "admin_mainmenu")
async def back_to_main_menu(callback: CallbackQuery, admin_repo: AdminRepository, user: User):
    await show_admin_panel(callback, admin_repo, user=user, sync=False)


@admin_base_router.callback_query(F.data.startswith("admin_"))
async def catch_other_admin_actions(callback: CallbackQuery, user: User):
    action = callback.data.split("_")[1]

    lang = user.language if user.language in ["ru", "en", "es"] else "en"
    kb = AdminInlineKb(lang=lang)

    alert_message = kb.get_text(f"alerts.{action}")
    if not alert_message:
        alert_message = kb.get_text("alerts.default", "Раздел в разработке...")

    await callback.answer(alert_message, show_alert=True)