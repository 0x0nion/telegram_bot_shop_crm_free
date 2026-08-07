# handlers/shop/shop.py
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from database.repositories.shop_repo import ShopRepository
from database.repositories.user_repo import UserRepository
from handlers.shop.render_product import show_product_card
from handlers.shop.render_shop import render_shop_menu


user_shop_router = Router()


@user_shop_router.callback_query(F.data.startswith("client_shop"))
async def shop_main(callback: CallbackQuery, shop_repo: ShopRepository, user_repo: UserRepository, state: FSMContext):
    await state.clear()
    await callback.answer()
    data_parts = callback.data.split("_")
    current_cat_id = None

    if len(data_parts) > 2 and data_parts[2] != "root":
        current_cat_id = int(data_parts[2])

    await render_shop_menu(
        event=callback,
        shop_repo=shop_repo,
        user_repo=user_repo,
        current_cat_id=current_cat_id
    )


@user_shop_router.callback_query(F.data.startswith("prev_") | F.data.startswith("next_"))
@user_shop_router.callback_query(F.data.startswith("client_item_"))
async def route_product_card(callback: CallbackQuery, shop_repo: ShopRepository, user_repo: UserRepository):
    await callback.answer()
    product_id = int(callback.data.split("_")[-1])
    user = await user_repo.get_user_with_cart(user_id=callback.from_user.id)

    await show_product_card(
        chat_id=callback.message.chat.id,
        product_id=product_id,
        shop_repo=shop_repo,
        cart_item=len(user.cart),
        bot=callback.bot,
        lang=user.language,
        old_message_id=callback.message.message_id
    )


@user_shop_router.callback_query(F.data.startswith("order_"))
async def order_product(callback: CallbackQuery, user_repo: UserRepository, shop_repo: ShopRepository, state: FSMContext):
    await callback.answer()
    product_id = int(callback.data.split("_")[-1])
    await user_repo.add_to_cart(user_id=callback.from_user.id, product_id=product_id)
    user = await user_repo.get_user_with_cart(user_id=callback.from_user.id)
    await show_product_card(
        chat_id=callback.message.chat.id,
        product_id=product_id,
        shop_repo=shop_repo,
        cart_item=len(user.cart),
        bot=callback.bot,
        lang=user.language,
        old_message_id=callback.message.message_id
    )
