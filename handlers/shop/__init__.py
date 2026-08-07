# handlers/shop/__init__.py
from aiogram import Router

from filters.admin import IsAdminFilter
from handlers.shop.shop import user_shop_router

user_shop_group_router = Router()

user_shop_group_router.include_routers(
    user_shop_router,
)
