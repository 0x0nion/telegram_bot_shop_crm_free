# handlers/admin/product_editor.py
import asyncio
from aiogram import Router, Bot
from aiogram.types import Message, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from database.repositories.shop_repo import ShopRepository
from keyboards.inline import InlineKb
from locales.locales import Locale


editor_router = Router()


def format_product_from_template(product, template: str) -> str:
    data = {
        "name": product.name,
        "description": product.description or "",
        "price": float(product.price),
        "unit": product.unit or ""
    }

    try:
        return template.format(**data)
    except Exception as e:
        return f"{product.name} - {product.price} $"


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

    template_product = locale.get_text('product_template')
    text = format_product_from_template(
        product=product,
        template=template_product
    )

    reply_markup = kb_manager.get_product_card_kb(
        product_id=product.id,
        category_id=product.category_id,
        prev_id=prev_product.id if prev_product else None,
        next_id=next_product.id if next_product else None,
        cart_item=cart_item,
        manager_url="https://t.me/username"
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
                    reply_markup=reply_markup,
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                )