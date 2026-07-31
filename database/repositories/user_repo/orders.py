from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload, joinedload

from database.models import OrderItem, Order
from database.models.cart import CartItem
from utils.logger import logger


class UserOrderMixin:

    async def create_order_from_cart(self, user_id: int, delivery_address: str | None = None,
                                     user_comment: str | None = None) -> Order | None:
        """
        Атомарно переносит товары из корзины в заказ и очищает корзину.
        """
        logger.info(f"Creating order from cart for user id={user_id}")
        user = await self.get_cart_with_products(user_id)

        if not user or not user.cart:
            return None

        total_price = 0.0
        order_items = []

        for cart_item in user.cart:
            current_price = float(cart_item.product.price)
            total_price += current_price * cart_item.quantity

            order_items.append(
                OrderItem(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price_at_purchase=current_price
                )
            )

        new_order = Order(
            user_id=user_id,
            total_price=total_price,
            delivery_address=delivery_address,
            user_comment=user_comment,
            status="pending",
            items=order_items
        )
        self.session.add(new_order)

        stmt = delete(CartItem).where(CartItem.user_id == user_id)
        await self.session.execute(stmt)

        await self.session.commit()

        stmt_select = (
            select(Order)
            .where(Order.id == new_order.id)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product)
            )
        )
        result = await self.session.execute(stmt_select)

        return result.unique().scalar_one_or_none()

    async def get_pending_orders(self, user_id: int):
        """
        Возвращает список активных заказов пользователя (со статусом pending).
        """
        stmt = (
            select(Order)
            .where(
                and_(
                    Order.user_id == user_id,
                    Order.status == "pending"
                )
            )
            .order_by(Order.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_order_with_items(self, order_id: int, user_id: int) -> Order | None:
        """
        Возвращает конкретный заказ пользователя со всеми вложенными товарами.
        """
        stmt = (
            select(Order)
            .options(
                selectinload(Order.items).joinedload(OrderItem.product)
            )
            .where(
                and_(
                    Order.id == order_id,
                    Order.user_id == user_id
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()