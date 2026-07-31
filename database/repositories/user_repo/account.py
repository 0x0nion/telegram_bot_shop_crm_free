from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models.cart import CartItem
from database.models.user import User
from utils.logger import logger


class UserAccountMixin:

    async def get_user(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_with_cart(self, user_id: int) -> User | None:
        stmt = (
            select(User)
            .options(
                selectinload(User.cart).selectinload(CartItem.product),
                selectinload(User.orders)
            )
            .where(User.id == user_id)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user_id: int) -> User:
        logger.info(f"Creating user id={user_id}")
        user = User(id=user_id)
        self.session.add(user)
        await self.session.commit()
        return user

    async def update_language(self, user_id: int, language: str) -> None:
        logger.info(f"Updating language for user id={user_id} to '{language}'")
        user = await self.get_user(user_id)
        if user:
            user.language = language
            await self.session.commit()

    async def get_or_create_user(self, tg_user) -> User | None:
        """
        Получает пользователя со связанной корзиной.
        Если его нет в БД — создает.
        """
        if not tg_user:
            return None

        user = await self.get_user_with_cart(tg_user.id)

        if not user:
            user = await self.create_user(user_id=tg_user.id)

        return user