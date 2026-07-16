# handlers/admin/base.py
import logging
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database.repositories.admin_repo import AdminRepository
from keyboards.inline import get_admin_keyboard

admin_base_router = Router()
logger = logging.getLogger(__name__)


# --- Вспомогательная функция для отображения меню ---
async def show_admin_panel(
    event: Message | CallbackQuery,
    admin_repo: AdminRepository,
    is_saved: bool = False,
    sync: bool = False
):
    """
    Единая точка входа для отображения админ-панели.
    sync=True вызывается только при инициализации сессии или после сохранения,
    чтобы навигация по меню не затирала текущий черновик админа.
    """
    if sync:
        await admin_repo.sync_to_temp(admin_id=event.from_user.id)

    text = "🔑 Панель администратора открыта:"
    if is_saved:
        text += "\n\n✅ Магазин обновлен!"

    try:
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text, reply_markup=get_admin_keyboard())
            await event.answer()
        else:
            await event.answer(text, reply_markup=get_admin_keyboard())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            if isinstance(event, CallbackQuery):
                await event.answer()
        else:
            raise e


@admin_base_router.message(Command("admin"))
async def cmd_admin(message: Message, admin_repo: AdminRepository):
    await show_admin_panel(message, admin_repo, sync=True)


@admin_base_router.callback_query(F.data == 'admin')
async def cb_admin(callback: CallbackQuery, admin_repo: AdminRepository):
    await show_admin_panel(callback, admin_repo, sync=True)


@admin_base_router.callback_query(F.data == 'admin_save_shop')
async def cb_admin_save(callback: CallbackQuery, admin_repo: AdminRepository):
    await admin_repo.commit_changes(admin_id=callback.from_user.id)
    await show_admin_panel(callback, admin_repo, is_saved=True, sync=True)


@admin_base_router.callback_query(F.data == "admin_mainmenu")
async def back_to_main_menu(callback: CallbackQuery, admin_repo: AdminRepository):
    """Возврат в корень панели без потери несохраненных изменений (sync=False)."""
    await show_admin_panel(callback, admin_repo, sync=False)


@admin_base_router.callback_query(F.data.startswith("admin_"))
async def catch_other_admin_actions(callback: CallbackQuery):
    """Ловим остальные разделы админки (Заглушки)."""
    action = callback.data.split("_")[1]

    messages = {
        "warehouse": "📦 Раздел 'Склад' в разработке...",
        "users": "👥 Раздел 'Юзеры' в разработке...",
        "workers": "⚒ Раздел 'Работники' в разработке...",
        "alert": "📢 Раздел 'Рассылка' в разработке...",
        "stat": "📈 Раздел 'Статистика' в разработке..."
    }

    await callback.answer(messages.get(action, "Раздел в разработке..."), show_alert=True)