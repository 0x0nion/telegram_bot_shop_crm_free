# handlers/admin/shop/render_shop_menu.py
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from database.models.user import User
from database.repositories.admin_repo import AdminRepository
from handlers.admin.utils import get_user_lang
from keyboards.admin_inline import AdminInlineKb
from locales.currencies import get_currency_symbol


async def render_shop_menu(
    event: CallbackQuery | Message,
    admin_repo: AdminRepository,
    current_cat_id: int | None,
    user: User,
    message_id_to_edit: int | None = None,
) -> None:
    """Универсальная и безопасная функция отрисовки интерфейса магазина."""
    admin_id = event.from_user.id
    lang = get_user_lang(user)
    kb = AdminInlineKb(lang=lang)

    current_cat = None
    has_description = False
    category_text = ""

    if current_cat_id:
        current_cat = await admin_repo.get_category_by_id(
            current_cat_id, use_temp=True, admin_id=admin_id
        )
        if current_cat:
            cat_name = (
                await admin_repo.get_locale_text(
                    entity_id=current_cat_id,
                    entity_type="category_name",
                    language_code=lang,
                    use_temp=True,
                    admin_id=admin_id,
                )
                or current_cat.name
            )

            category_text = (
                await admin_repo.get_locale_text(
                    entity_id=current_cat_id,
                    entity_type="category_description",
                    language_code=lang,
                    use_temp=True,
                    admin_id=admin_id,
                )
                or ""
            )

            shop_caption = kb.get_text(
                "category_title_template", "📁 Category: {name}\n"
            ).format(name=cat_name)
        else:
            shop_caption = kb.get_text(
                "category_not_found", "📁 Category: Not found\n"
            )
    else:
        shop_caption = kb.get_text("root_menu_title", "🏪 (Main Menu)\n")
        raw_category_text = (
            await admin_repo.get_locale_text(
                entity_id=0,
                entity_type="category_description",
                language_code=lang,
                use_temp=True,
                admin_id=admin_id,
            )
            or ""
        )

        # Проверяем реальное наличие пользовательского описания ДО подстановки дефолта
        if raw_category_text.strip():
            has_description = True
            category_text = raw_category_text
        else:
            category_text = kb.get_text(
                "root_menu_description",
                "Welcome to the admin catalog management.",
            )

    # Для подкатегорий проверяем description отдельно, если еще не проверили
    if current_cat_id and category_text.strip():
        has_description = True

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
            admin_id=admin_id,
        )
        category_names[cat.id] = loc_name or cat.name

    currency = get_currency_symbol()

    # Сборка текста сообщения
    body_parts = [shop_caption.strip()]
    if category_text.strip():
        body_parts.append(category_text.strip())

    base_text = "\n".join(body_parts)

    if db_products:
        products_text = "\n".join(
            [
                f"{product.id}: {product.name} - {product.price} {currency}"
                for product in db_products
            ]
        )
        text = f"{base_text}\n{'_' * 20}\n{products_text}"
    else:
        text = base_text

    parent_id = current_cat.parent_id if current_cat else None

    reply_markup = kb.get_shop_edit_kb(
        categories=db_categories,
        products=db_products,
        current_cat_id=current_cat_id,
        parent_id=parent_id,
        category_names=category_names,
        has_description=has_description,
    )

    chat_id = (
        event.message.chat.id
        if isinstance(event, CallbackQuery)
        else event.chat.id
    )
    msg_id = message_id_to_edit or (
        event.message.message_id if isinstance(event, CallbackQuery) else None
    )

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
                chat_id=chat_id, text=text, reply_markup=reply_markup
            )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            pass
        elif msg_id:
            try:
                await event.bot.delete_message(
                    chat_id=chat_id, message_id=msg_id
                )
            except Exception:
                pass
            await event.bot.send_message(
                chat_id=chat_id, text=text, reply_markup=reply_markup
            )
        else:
            raise e

    if isinstance(event, CallbackQuery):
        try:
            await event.answer()
        except TelegramBadRequest:
            pass