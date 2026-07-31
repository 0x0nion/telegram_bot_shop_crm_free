from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload

from database.models.cart import CartItem
from database.models.user import User
from utils.logger import logger


class UserCartMixin:

    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        logger.info(f"Adding product id={product_id} to cart for user id={user_id}")
        stmt = select(CartItem).where(
            and_(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        result = await self.session.execute(stmt)
        cart_item = result.scalar_one_or_none()

        if cart_item:
            cart_item.quantity += 1
        else:
            new_item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
            self.session.add(new_item)

        await self.session.commit()

    async def get_cart_with_products(self, user_id: int):
        stmt = (
            select(User)
            .options(selectinload(User.cart).joinedload(CartItem.product))
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return user

    async def update_cart_item(self, user_id: int, product_id: int, change: int):
        logger.info(f"Updating cart item product_id={product_id} for user id={user_id} with change={change}")
        stmt = select(CartItem).where(
            and_(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            return

        item.quantity += change

        if item.quantity <= 0:
            await self.session.delete(item)

        await self.session.commit()