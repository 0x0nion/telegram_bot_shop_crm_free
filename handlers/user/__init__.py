# handlers/user/__init__.py
from aiogram import Router

from handlers.user.user import user_router

user_group_router = Router()


user_group_router.include_routers(
    user_router
)
