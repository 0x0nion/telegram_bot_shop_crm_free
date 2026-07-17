# handlers/admin/__init__.py
from aiogram import Router

from filters.admin import IsAdminFilter
from .admin_main import admin_main_router
from handlers.admin.shop.categories import categories_router
from handlers.admin.shop.product_editor import editor_router
from handlers.admin.shop.products import products_router
from .shop import admin_shop_group_router


admin_group_router = Router()
admin_group_router.message.filter(IsAdminFilter())
admin_group_router.callback_query.filter(IsAdminFilter())


admin_group_router.include_routers(

    admin_shop_group_router,
    editor_router,
    products_router,
    categories_router,
    admin_main_router,
)
