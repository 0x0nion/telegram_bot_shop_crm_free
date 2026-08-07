# handlers/__init__.py
from aiogram import Router
from handlers.admin import admin_group_router
from handlers.order import user_order_group_router
from handlers.shop import user_shop_group_router
from handlers.cart import user_cart_group_router
from handlers.user import user_group_router

routers = Router()

routers.include_routers(
    admin_group_router,
    user_shop_group_router,
    user_cart_group_router,
    user_order_group_router,
    user_group_router,

)
