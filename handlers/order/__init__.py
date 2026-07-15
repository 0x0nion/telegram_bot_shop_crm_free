# handlers/order/__init__.py
from aiogram import Router

from filters.admin import IsAdminFilter
from handlers.order.order import user_order_router

user_order_group_router = Router()
# admin_group_router.message.filter(IsAdminFilter())
# admin_group_router.callback_query.filter(IsAdminFilter())

user_order_group_router.include_routers(
    user_order_router,
)
