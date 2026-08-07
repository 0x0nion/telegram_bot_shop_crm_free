# handlers/order/__init__.py
from aiogram import Router

from filters.admin import IsAdminFilter
from handlers.order.order import user_order_router

user_order_group_router = Router()

user_order_group_router.include_routers(
    user_order_router,
)
