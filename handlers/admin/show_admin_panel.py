# handlers/admin/show_admin_panel.py
from aiogram.types import CallbackQuery, Message

from database.models.user import User
from handlers.admin.utils import get_user_lang
from keyboards.admin_inline import AdminInlineKb
from src.core.ui import UIManager


async def show_admin_panel(
    event: Message | CallbackQuery,
    user: User,
    is_saved: bool = False,
) -> None:
    """Чистый UI-компонент (презентер) для отображения главного меню админ-панели."""
    lang = get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    # Формирование текста экрана
    text = kb.get_text("welcome_title", "🔑 Панель администратора открыта:")
    if is_saved:
        text += kb.get_text("shop_updated", "\n\n✅ Магазин обновлен!")

    reply_markup = kb.get_kb("admin_main_menu")

    await UIManager.show(
        event=event,
        text=text,
        reply_markup=reply_markup,
    )