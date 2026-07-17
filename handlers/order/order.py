import logging

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from database.models import User
from database.repositories.user_repo import UserRepository
from keyboards.inline import InlineKb
from locales.locales import Locale

logger = logging.getLogger(__name__)
user_order_router = Router()


@user_order_router.callback_query(F.data == "client_orders")
async def show_pending_orders(callback: CallbackQuery, user_repo: UserRepository, user: User):
    await callback.answer()
    user_id = callback.from_user.id

    locale = Locale(user.language)
    kb_manager = InlineKb(user.language)

    orders = await user_repo.get_pending_orders(user_id)

    if not orders:
        text = locale.get_text('user_empty_orders')
        reply_markup = kb_manager.get_main_kb(orders=len(user.orders), cart=len(user.cart))
    else:
        text = locale.get_text('user_active_orders_title')
        reply_markup = kb_manager.get_orders_kb(orders)

    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" in e.message:
            logger.info(f"User {user_id} double-clicked 'client_orders' (no changes).")
        else:
            raise


@user_order_router.callback_query(F.data.startswith("view_details_order_"))
async def view_order_details(callback: CallbackQuery, user_repo: UserRepository):
    user_id = callback.from_user.id
    user = await user_repo.get_user(user_id=user_id)

    locale = Locale(user.language)
    kb_manager = InlineKb(user.language)

    order_id = int(callback.data.split("_")[-1])

    order = await user_repo.get_order_with_items(order_id, user_id)

    if not order:
        await callback.answer(
            text=locale.get_text("user_order_not_found"),
            show_alert=True
        )
        return

    text = locale.format_order(order, template_key="user_order_details")

    reply_markup = kb_manager.get_kb("back_to_orders")

    await callback.message.edit_text(
        text=text,
        reply_markup=reply_markup,
    )
    await callback.answer()
