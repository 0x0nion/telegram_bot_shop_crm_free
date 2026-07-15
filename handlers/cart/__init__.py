# handlers/cart/__init__.py
from aiogram import Router

from filters.admin import IsAdminFilter
from handlers.cart.cart import user_cart_router

user_cart_group_router = Router()
# admin_group_router.message.filter(IsAdminFilter())
# admin_group_router.callback_query.filter(IsAdminFilter())

user_cart_group_router.include_routers(
    user_cart_router,
)
