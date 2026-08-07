from aiogram import Router
from .main import client_main_router
from .shop import user_shop_group_router
from .cart import user_cart_group_router
from .order import user_order_group_router

client_group_router = Router()
client_group_router.include_routers(
    user_shop_group_router,
    user_cart_group_router,
    user_order_group_router,
    client_main_router,
)