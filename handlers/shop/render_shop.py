# handlers/shop/render_shop.py
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest
from database.repositories.shop_repo import ShopRepository


from database.repositories.user_repo import UserRepository
from keyboards.inline import InlineKb
from locales.locales import Locale


async def render_shop_menu(
        event: CallbackQuery | Message,
        shop_repo: ShopRepository,
        user_repo: UserRepository,
        current_cat_id: int | None = None,
        message_id_to_edit: int | None = None
):
    """Универсальная и безопасная функция отрисовки интерфейса магазина с локализацией."""
    user_id = event.from_user.id

    user = await user_repo.get_user(user_id=user_id)
    lang = user.language if user else "en"

    locale = Locale(lang)
    kb_manager = InlineKb(lang)

    current_cat = None
    parent_id = None

    if current_cat_id:
        current_cat = await shop_repo.get_category_by_id(current_cat_id)
        if current_cat:
            shop_caption = locale.get_text("shop_category_title").format(cat_name=current_cat.name)
            parent_id = current_cat.parent_id
        else:
            shop_caption = locale.get_text("shop_category_not_found")
    else:
        shop_caption = locale.get_text("shop_main_menu_title")

    db_categories = await shop_repo.get_categories_by_parent(parent_id=current_cat_id)
    db_products = await shop_repo.get_products_by_category(category_id=current_cat_id)

    if db_products:
        product_template = locale.get_text("shop_product_line")
        products_text = "\n".join([
            product_template.format(id=product.id, name=product.name, price=float(product.price))
            for product in db_products
        ])
        text = f"{shop_caption}{'_' * 20}\n{products_text}"
    else:
        empty_text = locale.get_text("shop_empty_category")
        text = f"{shop_caption}"

    reply_markup = kb_manager.get_shop_keyboard(
        categories=db_categories,
        products=db_products,
        current_cat_id=current_cat_id,
        parent_id=parent_id
    )

    chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
    msg_id = message_id_to_edit or (event.message.message_id if isinstance(event, CallbackQuery) else None)

    try:
        if msg_id:
            await event.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=reply_markup,
            )
        else:
            await event.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
            )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        elif msg_id:
            try:
                await event.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception:
                pass
            await event.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
            )
        else:
            raise e

    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except TelegramBadRequest:
            pass