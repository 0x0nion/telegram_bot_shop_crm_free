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
            # 1. Загружаем локализованное имя категории для заголовка
            cat_name = await admin_repo.get_locale_text(
                entity_id=current_cat_id,
                entity_type="category_name",
                language_code=lang,
                use_temp=True,
                admin_id=admin_id
            ) or current_cat.name

            # 2. Загружаем описание категории
            category_text = await admin_repo.get_locale_text(
                entity_id=current_cat_id,
                entity_type="category_description",
                language_code=lang,
                use_temp=True,
                admin_id=admin_id
            ) or ""

            shop_caption = kb.get_text("category_title_template", "📁 Category: {name}\n").format(name=cat_name)
        else:
            shop_caption = kb.get_text("category_not_found", "📁 Category: Not found\n")
            category_text = ""
    else:
        shop_caption = kb.get_text("root_menu_title", "🏪 (Main Menu)\n")

        # Загружаем описание для корня (entity_id = 0)
        category_text = await admin_repo.get_locale_text(
            entity_id=0,
            entity_type="category_description",
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

    # Собираем словарь локализованных имен для кнопок категорий
    category_names: dict[int, str] = {}
    for cat in db_categories:
        loc_name = await admin_repo.get_locale_text(
            entity_id=cat.id,
            entity_type="category_name",
            language_code=lang,
            use_temp=True,
            admin_id=admin_id
        )
        category_names[cat.id] = loc_name or cat.name

    if db_products:
        products_text = "\n".join([
            f"{product.id}: {product.name} - {product.price}"
            for product in db_products
        ])
        text = f"{shop_caption}{category_text}\n{'_' * 20}\n{products_text}"
    else:
        text = f"{shop_caption}{category_text}"

    parent_id = current_cat.parent_id if current_cat else None

    # Передаем динамические имена кнопок в клавиатуру
    reply_markup = kb.get_shop_edit_kb(
        categories=db_categories,
        products=db_products,
        current_cat_id=current_cat_id,
        parent_id=parent_id,
        category_names=category_names
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