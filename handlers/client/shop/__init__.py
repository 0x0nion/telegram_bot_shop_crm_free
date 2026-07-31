# handlers/client/shop/__init__.py
from aiogram import Router

from handlers.client.shop.shop import user_shop_router

user_shop_group_router = Router()

user_shop_group_router.include_routers(
    user_shop_router,
)
