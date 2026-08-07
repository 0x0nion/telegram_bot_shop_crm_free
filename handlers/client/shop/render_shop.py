# handlers/client/shop/render_shop.py
from aiogram.types import CallbackQuery, Message

from database.repositories.shop_repo import ShopRepository
from database.repositories.user_repo import UserRepository
from keyboards.inline import InlineKb
from locales.currencies import get_currency_symbol
from locales.locales import Locale
from src.core.ui import UIManager


async def render_shop_menu(
    event: CallbackQuery | Message,
    shop_repo: ShopRepository,
    user_repo: UserRepository,
    current_cat_id: int | None = None,
    message_id_to_edit: int | None = None,
) -> None:
    """Универсальная и безопасная функция отрисовки интерфейса магазина для клиента."""
    user_id = event.from_user.id
    user = await user_repo.get_user(user_id=user_id)
    lang = user.language if user and user.language else "ru"

    locale = Locale(lang)
    kb_manager = InlineKb(lang)
    currency = get_currency_symbol()

    current_cat = None
    parent_id = None
    category_text = ""

    # 1. Загрузка данных текущей категории и ее локализаций из БД
    if current_cat_id:
        current_cat = await shop_repo.get_category_by_id(current_cat_id)
        if current_cat:
            parent_id = current_cat.parent_id

            # Локализованное название категории
            cat_name = await user_repo.get_locale_text(
                entity_type="category_name",
                entity_id=current_cat_id,
                lang_code=lang,
            ) or current_cat.name

            # Локализованное описание категории
            category_text = await user_repo.get_locale_text(
                entity_type="category_description",
                entity_id=current_cat_id,
                lang_code=lang,
            ) or ""

            shop_caption = locale.get_text("shop_category_title").format(cat_name=cat_name)
        else:
            shop_caption = locale.get_text("shop_category_not_found")
    else:
        # Корневое меню магазина (entity_id = 0)
        shop_caption = locale.get_text("shop_main_menu_title")
        category_text = await user_repo.get_locale_text(
            entity_type="category_description",
            entity_id=0,
            lang_code=lang,
        ) or ""

    # 2. Получение списка дочерних категорий и товаров
    db_categories = await shop_repo.get_categories_by_parent(parent_id=current_cat_id)
    db_products = await shop_repo.get_products_by_category(category_id=current_cat_id)

    # 3. Подгрузка локализованных имен для кнопок подкатегорий
    category_names: dict[int, str] = {}
    for cat in db_categories:
        loc_name = await user_repo.get_locale_text(
            entity_type="category_name",
            entity_id=cat.id,
            lang_code=lang,
        )
        category_names[cat.id] = loc_name or cat.name

    # 4. Формирование итогового текста сообщения
    body_parts = [shop_caption.strip()]
    if category_text.strip():
        body_parts.append(category_text.strip())

    base_text = "\n\n".join(body_parts)

    if db_products:
        product_template = locale.get_text("shop_product_line")
        products_lines = []
        for product in db_products:
            raw_price = float(product.price) if product.price is not None else 0.0
            try:
                # Пробуем передать price как float и currency отдельно (если шаблон вида "{name} — {price:.2f} {currency}")
                line = product_template.format(
                    id=product.id,
                    name=product.name,
                    price=raw_price,
                    currency=currency,
                )
            except (ValueError, KeyError):
                # Фолбэк на случай шаблона без спецификаторов типов ({price} {currency})
                line = product_template.format(
                    id=product.id,
                    name=product.name,
                    price=f"{raw_price:g}",
                    currency=currency,
                )
            products_lines.append(line)

        products_text = "\n".join(products_lines)
        text = f"{base_text}\n{'_' * 20}\n{products_text}"
    else:
        text = base_text

    # 5. Сборка клавиатуры с учетом локализованных названий категорий
    reply_markup = kb_manager.get_shop_keyboard(
        categories=db_categories,
        products=db_products,
        current_cat_id=current_cat_id,
        parent_id=parent_id,
        category_names=category_names,
    )

    # 6. Безопасный рендеринг через UIManager
    await UIManager.show(
        event=event,
        text=text,
        reply_markup=reply_markup,
        message_id_to_edit=message_id_to_edit,
    )