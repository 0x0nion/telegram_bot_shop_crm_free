# handlers/admin/__init__.py
from aiogram import Router

from filters.admin import IsAdminFilter
from .categories import categories_router
from .base import admin_base_router
from .product_editor import editor_router
from .products import products_router

admin_group_router = Router()
admin_group_router.message.filter(IsAdminFilter())
admin_group_router.callback_query.filter(IsAdminFilter())


admin_group_router.include_routers(
    editor_router,
    products_router,
    categories_router,
    admin_base_router
)
