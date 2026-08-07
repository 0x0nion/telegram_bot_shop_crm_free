from sqlalchemy import and_
from sqlalchemy.orm import selectinload, joinedload

from database.models import OrderItem, Order
from database.models.cart import CartItem
from database.repositories.base_repo import BaseRepository
from utils.logger import logger


class UserOrderMixin:

    @property
    def _order_repo(self) -> BaseRepository[Order]:
        return BaseRepository(Order, self.session)

    @property
    def _cart_repo(self) -> BaseRepository[CartItem]:
        return BaseRepository(CartItem, self.session)

    async def create_order_from_cart(
        self,
        user_id: int,
        delivery_address: str | None = None,
        user_comment: str | None = None
    ) -> Order | None:
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

        # 1. Создаем заказ без коммита
        new_order = await self._order_repo.create_without_commit(
            user_id=user_id,
            total_price=total_price,
            delivery_address=delivery_address,
            user_comment=user_comment,
            status="pending",
            items=order_items
        )

        # 2. Очищаем элементы корзины через ORM-удаление объектов
        # Это гарантирует, что SQLAlchemy применит изменения к объекту user.cart в памяти
        for item in list(user.cart):
            await self.session.delete(item)

        # 3. Фиксируем транзакцию (заказ создан, корзина в БД и памяти очищена)
        await self.session.commit()

        # 4. Инвалидируем состояние юзера в сессии, чтобы при следующем запросе
        # сессия гарантированно подгрузила пустую корзину из БД
        self.session.expire(user)

        # 5. Возвращаем созданный заказ со всеми объектами
        return await self._order_repo.get_by_id(
            new_order.id,
            options=[selectinload(Order.items).joinedload(OrderItem.product)]
        )

    async def get_pending_orders(self, user_id: int) -> list[Order]:
        return await self._order_repo.get_all(
            and_(
                Order.user_id == user_id,
                Order.status == "pending"
            ),
            options=[selectinload(Order.items).joinedload(OrderItem.product)],
            order_by=Order.created_at.desc()
        )

    async def get_order_with_items(self, order_id: int, user_id: int) -> Order | None:
        options = [selectinload(Order.items).joinedload(OrderItem.product)]
        return await self._order_repo.get_one(
            and_(
                Order.id == order_id,
                Order.user_id == user_id
            ),
            options=options
        )