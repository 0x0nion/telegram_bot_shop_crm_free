from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery

from database.repositories.admin_repo import AdminRepository
from keyboards.admin_inline import AdminInlineKb
from database.models.user import User


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