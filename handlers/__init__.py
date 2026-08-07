from aiogram import Router
from handlers.admin import admin_group_router
from handlers.client import client_group_router

routers = Router()
routers.include_routers(
    admin_group_router,
    client_group_router,
)