from typing import Union
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from database.repositories.user_repo import UserRepository
from keyboards.inline import InlineKb
from locales.locales import Locale


async def render_cart(
        event: Union[CallbackQuery, Message],
        user_repo: UserRepository,
        state: FSMContext
):
    bot = event.bot
    chat_id = event.message.chat.id if isinstance(event, CallbackQuery) else event.chat.id
    user_id = event.from_user.id

    if isinstance(event, CallbackQuery):
        await event.answer()

    user = await user_repo.get_cart_with_products(user_id)
    lang = user.language if user else "en"

    locale = Locale(lang)
    kb_manager = InlineKb(lang)

    state_data = await state.get_data()
    cart_msg_id = state_data.get("cart_message_id")

    address = state_data.get("delivery_address")
    comment = state_data.get("user_comment")

    if not user or not user.cart:
        text = locale.get_text("cart_empty")
        try:
            if cart_msg_id:
                await bot.edit_message_text(chat_id=chat_id, message_id=cart_msg_id, text=text, parse_mode="HTML")
                return
        except TelegramBadRequest:
            pass

        new_msg = await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
        await state.update_data(cart_message_id=new_msg.message_id)
        return

    subtotal = sum(item.quantity * float(item.product.price) for item in user.cart)

    text_blocks = [locale.get_text("cart_title")]

    item_template = locale.get_text("cart_item_line")
    for item in user.cart:
        product_name = item.product.name if item.product else "Deleted Product"
        item_total = item.quantity * float(item.product.price)
        text_blocks.append(
            item_template.format(
                name=product_name,
                quantity=item.quantity,
                item_total=item_total
            )
        )

    text_blocks.append(locale.get_text("cart_summary_subtotal").format(subtotal=subtotal))

    if address:
        addr_text = address
    else:
        addr_text = locale.get_text("cart_address_not_specified")
    text_blocks.append(locale.get_text("cart_address_label").format(address=addr_text))

    comm_text = comment if comment else locale.get_text("cart_comment_not_specified")
    text_blocks.append(locale.get_text("cart_comment_label").format(comment=comm_text))

    text = "".join(text_blocks)

    markup = kb_manager.get_cart_kb(cart_items=user.cart, has_address=bool(address))

    try:
        if cart_msg_id:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=cart_msg_id,
                text=text,
                reply_markup=markup,
            )
        else:
            new_msg = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=markup,
            )
            await state.update_data(cart_message_id=new_msg.message_id)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            # Если сообщение было удалено или возникла иная ошибка — отправляем новое
            new_msg = await bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=markup,
            )
            await state.update_data(cart_message_id=new_msg.message_id)