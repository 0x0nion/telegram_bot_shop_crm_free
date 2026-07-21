# /handlers/admin/admin_main.py
import logging
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database.repositories.admin_repo import AdminRepository
from handlers.admin.show_admin_panel import show_admin_panel
from keyboards.admin_inline import AdminInlineKb
from database.models.user import User

admin_main_router = Router()
logger = logging.getLogger(__name__)


@admin_main_router.message(Command("admin"))
async def cmd_admin(message: Message, admin_repo: AdminRepository, user: User):
    await show_admin_panel(message, admin_repo, user=user, sync=True)


@admin_main_router.callback_query(F.data == 'admin')
async def cb_admin(callback: CallbackQuery, admin_repo: AdminRepository, user: User):
    await show_admin_panel(callback, admin_repo, user=user, sync=True)


@admin_main_router.callback_query(F.data == 'admin_save_shop')
async def cb_admin_save(callback: CallbackQuery, admin_repo: AdminRepository, user: User):
    await admin_repo.commit_changes(admin_id=callback.from_user.id)
    await show_admin_panel(callback, admin_repo, user=user, is_saved=True, sync=True)


@admin_main_router.callback_query(F.data == "admin_mainmenu")
async def back_to_main_menu(callback: CallbackQuery, admin_repo: AdminRepository, user: User):
    await show_admin_panel(callback, admin_repo, user=user, sync=False)


@admin_main_router.callback_query(F.data.startswith("admin_"))
async def catch_other_admin_actions(callback: CallbackQuery, user: User):
    action = callback.data.split("_")[1]

    lang = user.language if user.language in ["ru", "en", "es"] else "en"
    kb = AdminInlineKb(lang=lang)

    alert_message = kb.get_text(f"alerts.{action}")
    if not alert_message:
        alert_message = kb.get_text("alerts.default", "Раздел в разработке...")

    await callback.answer(alert_message, show_alert=True)