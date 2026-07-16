# handlers/admin/common.py
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.repositories.admin_repo import AdminRepository
from aiogram.exceptions import TelegramBadRequest


async def render_shop_menu(
        event: CallbackQuery | Message,
        admin_repo: AdminRepository,
        current_cat_id: int | None,
        message_id_to_edit: int | None = None
):
    """Универсальная и безопасная функция отрисовки интерфейса магазина."""
    admin_id = event.from_user.id
    current_cat = None

    if current_cat_id:
        current_cat = await admin_repo.get_category_by_id(
            current_cat_id, use_temp=True, admin_id=admin_id
        )
        shop_caption = f"📁 Категория: {current_cat.name}\n" if current_cat else "📁 Категория: Не найдена\n"
    else:
        shop_caption = "🏪 (Главное меню)\n"

    db_categories = await admin_repo.get_categories_by_parent(
        parent_id=current_cat_id, use_temp=True, admin_id=admin_id
    )
    db_products = await admin_repo.get_products_by_category(
        category_id=current_cat_id, use_temp=True, admin_id=admin_id
    )

    products_text = "\n".join([
        f"{product.id}: {product.name} - {product.price}"
        for product in db_products
    ])
    text = f"{shop_caption}{'_' * 20}\n{products_text}" if db_products else f"{shop_caption}\nЗдесь пока нет товаров."

    builder = InlineKeyboardBuilder()

    if current_cat_id and current_cat:
        parent_to_go = current_cat.parent_id if current_cat.parent_id else "root"
        builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_shop_{parent_to_go}"))
    else:
        builder.row(InlineKeyboardButton(text="⬅️ В главное меню", callback_data="admin_mainmenu"))

    for category in db_categories:
        builder.row(
            InlineKeyboardButton(text=f"📁 {category.name}", callback_data=f"admin_shop_{category.id}"),
            InlineKeyboardButton(text="❌ Удалить", callback_data=f"admin_del_cat_{category.id}")
        )

    for product in db_products:
        builder.row(
            InlineKeyboardButton(text=f"📦 {product.name}", callback_data=f"admin_item_{product.id}"),
            InlineKeyboardButton(text="❌ Удалить", callback_data=f"admin_del_item_{product.id}")
        )

    cat_suffix = f"_{current_cat_id}" if current_cat_id else "_root"
    builder.row(InlineKeyboardButton(text="🟢 Добавить подкатегорию", callback_data=f"admin_addcat{cat_suffix}"))
    builder.row(InlineKeyboardButton(text="🔴 Добавить товар сюда", callback_data=f"admin_add_item{cat_suffix}"))
    builder.row(InlineKeyboardButton(text="💾 Сохранить изменения", callback_data="admin_save_shop"))

    chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
    msg_id = message_id_to_edit or (event.message.message_id if isinstance(event, CallbackQuery) else None)

    try:
        if msg_id:
            await event.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text, reply_markup=builder.as_markup())
        else:
            await event.bot.send_message(chat_id=chat_id, text=text, reply_markup=builder.as_markup())
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        elif msg_id:
            try:
                await event.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass
            await event.bot.send_message(chat_id=chat_id, text=text, reply_markup=builder.as_markup())
        else:
            raise e

    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except TelegramBadRequest:
            pass