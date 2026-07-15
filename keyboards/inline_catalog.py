from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models.category import Category
from database.models.product import Product


def get_catalog_keyboard(
        categories: list[Category],
        products: list[Product] = None,
        parent_id: int | None = None
) -> InlineKeyboardMarkup:
    """Универсальный строитель клавиатуры для навигации по магазину"""
    builder = InlineKeyboardBuilder()

    # 1. Выводим категории (если есть подкатегории)
    for category in categories:
        builder.row(InlineKeyboardButton(
            text=f"📁 {category.name}",
            callback_data=f"user_cat_{category.id}"
        ))

    # 2. Выводим товары в этой категории (если переданы)
    if products:
        for product in products:
            builder.row(InlineKeyboardButton(
                text=f"🍏 {product.name} — {product.price} руб.",
                callback_data=f"user_prod_{product.id}"
            ))

    # 3. Управляющие кнопки (Назад / В главное меню)
    navigation_buttons = []
    if parent_id is not None:
        # Если мы внутри подкатегории, кнопка "Назад" ведет к родителю
        navigation_buttons.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="user_catalog_root" if parent_id == 0 else f"user_cat_{parent_id}"
        ))

    navigation_buttons.append(InlineKeyboardButton(
        text="🛒 Корзина",
        callback_data="user_cart"
    ))

    # Добавляем навигационный ряд
    builder.row(*navigation_buttons)

    return builder.as_markup()


def get_product_card_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для карточки отдельного товара"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить в корзину", callback_data="TODO_add_to_cart"),
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к товарам", callback_data=f"user_cat_{category_id}")
    )
    return builder.as_markup()