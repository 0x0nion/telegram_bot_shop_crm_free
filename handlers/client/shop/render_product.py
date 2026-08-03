import asyncio
from aiogram import Bot
from aiogram.types import Message, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from database.repositories.shop_repo import ShopRepository
from keyboards.inline import InlineKb
from locales.locales import Locale
from locales.units import get_unit_label  # Единая логика с админкой!
from locales.currencies import get_currency_symbol  # Единая логика с админкой!
from utils.logger import logger


def format_product_from_template(product, locale: Locale, lang: str = "en") -> str:
    """Динамический сборщик текста карточки товара с учетом локализованных полей."""
    template = locale.get_text('product_template')
    if not template or template in ('product_template', 'XXX'):
        template = "<b>{name}</b>\n\n{description}\n\nЦена: {price} {currency} / {unit}"

    # 1. Единицы измерения через тот же модуль, что и в админке
    unit_val = get_unit_label(product.unit, lang=lang)

    # 2. Описание товара
    no_desc_text = locale.get_text("no_description")
    desc_fallback = no_desc_text if (no_desc_text and no_desc_text not in ("no_description", "XXX")) else ""
    desc_val = product.description or desc_fallback

    # 3. Символ валюты
    currency_code = getattr(product, "currency", None)
    currency_val = get_currency_symbol(currency_code) if currency_code else locale.get_text("currency_symbol")
    if not currency_val or currency_val in ("currency_symbol", "XXX"):
        currency_val = "$"

    data = {
        "name": product.name,
        "description": desc_val,
        "price": float(product.price or 0.0),
        "currency": currency_val,
        "unit": unit_val
    }

    try:
        return template.format(**data)
    except Exception as e:
        logger.error(f"[SHOP UI] Error formatting product template for id={product.id}: {e}")
        return f"{product.name} - {product.price} {currency_val}"


async def self_destruct(message: Message, seconds: int = 3):
    """Безопасно удаляет сообщение с ошибкой через заданное время."""
    await asyncio.sleep(seconds)
    try:
        await message.delete()
    except TelegramBadRequest:
        pass


async def show_product_card(
        chat_id: int,
        product_id: int,
        shop_repo: ShopRepository,
        bot: Bot,
        lang: str = 'en',
        cart_item: int = 0,
        old_message_id: int = None
):
    """Универсальная локализованная функция для отрисовки карточки товара."""
    logger.info(f"Showing product card id={product_id} for chat_id={chat_id}")
    product = await shop_repo.get_product_by_id(product_id)
    if not product:
        return

    next_product = await shop_repo.get_next_product(
        category_id=product.category_id,
        current_product_id=product.id
    )
    prev_product = await shop_repo.get_prev_product(
        category_id=product.category_id,
        current_product_id=product.id
    )

    locale = Locale(lang)
    kb_manager = InlineKb(lang)

    # 1. Сборка текста через динамический сборщик с передачей lang
    text = format_product_from_template(
        product=product,
        locale=locale,
        lang=lang
    )

    # 2. Валидация URL менеджера
    manager_url = locale.get_text("manager_url")
    if not manager_url or manager_url in ("manager_url", "XXX") or not (manager_url.startswith("http://") or manager_url.startswith("https://")):
        manager_url = "https://t.me/username"

    reply_markup = kb_manager.get_product_card_kb(
        product_id=product.id,
        category_id=product.category_id,
        prev_id=prev_product.id if prev_product else None,
        next_id=next_product.id if next_product else None,
        cart_item=cart_item,
        manager_url=manager_url
    )

    try:
        if product.image_id:
            await bot.edit_message_media(
                chat_id=chat_id,
                message_id=old_message_id,
                media=InputMediaPhoto(
                    media=product.image_id,
                    caption=text,
                    parse_mode="HTML"
                ),
                reply_markup=reply_markup
            )
        else:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=old_message_id,
                text=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            try:
                await bot.delete_message(
                    chat_id=chat_id,
                    message_id=old_message_id
                )
            except Exception:
                pass

            if product.image_id:
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=product.image_id,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=reply_markup,
                )