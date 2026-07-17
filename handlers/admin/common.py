from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from database.repositories.admin_repo import AdminRepository
from keyboards.admin_inline import AdminInlineKb  # Оригинальный импорт
from database.models.user import User


async def render_shop_menu(
        event: CallbackQuery | Message,
        admin_repo: AdminRepository,
        current_cat_id: int | None,
        user: User,  # Обязательно передаем объект юзера
        message_id_to_edit: int | None = None
):
    """Универсальная и безопасная функция отрисовки интерфейса магазина."""
    admin_id = event.from_user.id
    current_cat = None

    # Всегда берем язык из БД, фолбек на "en"
    lang = user.language if user.language in ["ru", "en", "es"] else "en"
    kb = AdminInlineKb(lang=lang)

    # 1. Формируем локализованный заголовок категории
    if current_cat_id:
        current_cat = await admin_repo.get_category_by_id(
            current_cat_id, use_temp=True, admin_id=admin_id
        )
        if current_cat:
            shop_caption = kb.get_text("category_title_template", "📁 Category: {name}\n").format(name=current_cat.name)
        else:
            shop_caption = kb.get_text("category_not_found", "📁 Category: Not found\n")
    else:
        shop_caption = kb.get_text("root_menu_title", "🏪 (Main Menu)\n")

    db_categories = await admin_repo.get_categories_by_parent(
        parent_id=current_cat_id, use_temp=True, admin_id=admin_id
    )
    db_products = await admin_repo.get_products_by_category(
        category_id=current_cat_id, use_temp=True, admin_id=admin_id
    )

    # 2. Собираем описание товаров
    if db_products:
        products_text = "\n".join([
            f"{product.id}: {product.name} - {product.price}"
            for product in db_products
        ])
        text = f"{shop_caption}{'_' * 20}\n{products_text}"
    else:
        no_prod_message = kb.get_text("no_products", "\nThere are no products here yet.")
        text = f"{shop_caption}{no_prod_message}"

    # 3. Генерируем клавиатуру через метод нашего билдера
    parent_id = current_cat.parent_id if current_cat else None
    reply_markup = kb.get_shop_edit_kb(
        categories=db_categories,
        products=db_products,
        current_cat_id=current_cat_id,
        parent_id=parent_id
    )

    # 4. Отправляем или редактируем сообщение
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