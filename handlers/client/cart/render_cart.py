# handlers/client/cart/render_cart.py
from typing import Union
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from database.repositories.user_repo import UserRepository
from keyboards.inline import InlineKb
from locales.locales import Locale
from src.core.ui import UIManager


async def render_cart(
        event: Union[CallbackQuery, Message],
        user_repo: UserRepository,
        state: FSMContext
):
    user = await user_repo.get_or_create_user(event.from_user)
    lang = user.language if user else "en"

    locale = Locale(lang)
    kb_manager = InlineKb(lang)

    state_data = await state.get_data()
    cart_msg_id = state_data.get("cart_message_id")

    # Корзина пуста
    if not user or not user.cart:
        text = locale.get_text("cart_empty")
        orders_count = len(user.orders) if user and hasattr(user, "orders") else 0
        main_kb = InlineKb(lang).get_main_kb(orders=orders_count, cart=0)

        sent_msg = await UIManager.show(
            event=event,
            text=text,
            reply_markup=main_kb,
            message_id_to_edit=cart_msg_id
        )
        await state.update_data(cart_message_id=sent_msg.message_id)
        return

    # Расчет содержимого корзины
    address = state_data.get("delivery_address")
    comment = state_data.get("user_comment", "")
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

    addr_text = address if address else locale.get_text("cart_address_not_specified")
    text_blocks.append(locale.get_text("cart_address_label").format(address=addr_text))

    comm_text = comment if comment else locale.get_text("cart_comment_not_specified")
    text_blocks.append(locale.get_text("cart_comment_label").format(comment=comm_text))

    text = "".join(text_blocks)
    markup = kb_manager.get_cart_kb(cart_items=user.cart, has_address=bool(address))

    # Отрисовка через UIManager и обновление cart_message_id в FSM
    sent_msg = await UIManager.show(
        event=event,
        text=text,
        reply_markup=markup,
        message_id_to_edit=cart_msg_id
    )
    await state.update_data(cart_message_id=sent_msg.message_id)