from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from database.repositories.admin_repo import AdminRepository
from keyboards.admin_inline import AdminInlineKb
from database.models.user import User


async def render_shop_menu(
        event: CallbackQuery | Message,
        admin_repo: AdminRepository,
        current_cat_id: int | None,
        user: User,
        message_id_to_edit: int | None = None
):
    """Универсальная и безопасная функция отрисовки интерфейса магазина."""
    admin_id = event.from_user.id
    current_cat = None

    lang = user.language if user.language in ["ru", "en", "es"] else "en"
    kb = AdminInlineKb(lang=lang)

    if current_cat_id:
        current_cat = await admin_repo.get_category_by_id(
            current_cat_id, use_temp=True, admin_id=admin_id
        )
        if current_cat:
            shop_caption = kb.get_text("category_title_template", "📁 Category: {name}\n").format(name=current_cat.name)

            # Загружаем локализованный текст/описание категории из временной таблицы локалей (entity_type="category")
            category_text = await admin_repo.get_locale_text(
                entity_id=current_cat_id,
                entity_type="category",
                language_code=lang,
                use_temp=True,
                admin_id=admin_id
            ) or current_cat.name
        else:
            shop_caption = kb.get_text("category_not_found", "📁 Category: Not found\n")
            category_text = ""
    else:
        shop_caption = kb.get_text("root_menu_title", "🏪 (Main Menu)\n")
        # Загружаем кастомное описание для корня (entity_id = 0) из временной таблицы локалей (entity_type="category")
        category_text = await admin_repo.get_locale_text(
            entity_id=0,
            entity_type="category",
            language_code=lang,
            use_temp=True,
            admin_id=admin_id
        ) or kb.get_text("root_menu_description", "Welcome to the admin catalog management.")

    db_categories = await admin_repo.get_categories_by_parent(
        parent_id=current_cat_id, use_temp=True, admin_id=admin_id
    )
    db_products = await admin_repo.get_products_by_category(
        category_id=current_cat_id, use_temp=True, admin_id=admin_id
    )

    if db_products:
        products_text = "\n".join([
            f"{product.id}: {product.name} - {product.price}"
            for product in db_products
        ])
        text = f"{shop_caption}{category_text}\n{'_' * 20}\n{products_text}"
    else:
        text = f"{shop_caption}{category_text}"

    parent_id = current_cat.parent_id if current_cat else None
    reply_markup = kb.get_shop_edit_kb(
        categories=db_categories,
        products=db_products,
        current_cat_id=current_cat_id,
        parent_id=parent_id
    )

    chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
    msg_id = message_id_to_edit or (event.message.message_id if isinstance(event, CallbackQuery) else None)

    try:
        if msg_id:
            await event.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=text, reply_markup=reply_markup)
        else:
            await event.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        elif msg_id:
            try:
                await event.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass
            await event.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
        else:
            raise e

    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except TelegramBadRequest:
            pass