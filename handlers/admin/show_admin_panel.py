# handlers/admin/show_admin_panel.py
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from database.models.user import User
from database.repositories.admin_repo import AdminRepository
from handlers.admin.utils import get_user_lang
from keyboards.admin_inline import AdminInlineKb


async def show_admin_panel(
    event: Message | CallbackQuery,
    admin_repo: AdminRepository,
    user: User,
    is_saved: bool = False,
    sync: bool = False,
) -> None:
    """Единая точка входа для отображения админ-панели."""
    admin_id = event.from_user.id

    if sync:
        await admin_repo.sync_to_temp(admin_id=admin_id)

    lang = get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    # Формирование текста
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
        if "message is not modified" in str(e) and isinstance(
            event, CallbackQuery
        ):
            await event.answer()
        else:
            raise e