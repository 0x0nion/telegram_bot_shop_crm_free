# database/repositories/user_repo.py
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload, joinedload

from database.models import OrderItem, Order
from database.models.cart import CartItem
from database.repositories.base_repo import BaseRepository
from database.models.user import User


class UserRepository(BaseRepository):
    # --- Методы для работы с Пользователями ---

    async def get_user(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_with_cart(self, user_id: int) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.cart))  # ЭТО КЛЮЧЕВОЙ МОМЕНТ
            .where(User.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user_id: int) -> User:
        user = User(id=user_id)
        self.session.add(user)
        await self.session.commit()
        return user

    async def update_language(self, user_id: int, language: str) -> None:
        user = await self.get_user(user_id)
        if user:
            user.language = language
            await self.session.commit()

    async def get_or_create_user(self, tg_user) -> User | None:
        """
        Получает пользователя со связанной корзиной.
        Если его нет в БД — создает. Если изменился username — обновляет.
        """
        if not tg_user:
            return None

        # Ищем пользователя сразу с подгрузкой корзины
        user = await self.get_user_with_cart(tg_user.id)

        if not user:
            # Если не нашли — создаем
            user = await self.create_user(user_id=tg_user.id)
            # Чтобы в только что созданном объекте была пустая коллекция cart, а не ошибка
            user.cart = []

        return user



    async def add_to_cart(self, user_id: int, product_id: int) -> None:
        # 1. Ищем, есть ли такой товар у пользователя в корзине
        stmt = select(CartItem).where(
            and_(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        result = await self.session.execute(stmt)
        cart_item = result.scalar_one_or_none()

        if cart_item:
            # 2. Если есть — просто увеличиваем количество
            cart_item.quantity += 1
        else:
            # 3. Если нет — создаем новую запись
            new_item = CartItem(user_id=user_id, product_id=product_id, quantity=1)
            self.session.add(new_item)

        # 4. Сохраняем изменения
        await self.session.commit()

    # В UserRepository
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
        # 1. Находим товар в корзине через SQLAlchemy
        stmt = select(CartItem).where(
            and_(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()

        if not item:
            return

        # 2. Изменяем количество
        item.quantity += change

        if item.quantity <= 0:
            # 3. Если количество стало 0 или меньше — удаляем запись
            await self.session.delete(item)

        # 4. Сохраняем изменения (commit фиксирует и обновление, и удаление)
        await self.session.commit()

    async def create_order_from_cart(self, user_id: int, delivery_address: str | None = None,
                                     user_comment: str | None = None) -> Order | None:
        """
        Атомарно переносит товары из корзины в заказ и очищает корзину.
        """
        # 1. Получаем корзину со всеми товарами и их ценами (используем твой готовый метод)
        user = await self.get_cart_with_products(user_id)

        # Если корзины нет или она пуста
        if not user or not user.cart:
            return None

        total_price = 0.0
        order_items = []

        # 2. Формируем список покупок и считаем итоговую сумму
        for cart_item in user.cart:
            # Обязательно фиксируем цену товара на момент покупки
            current_price = float(cart_item.product.price)
            total_price += current_price * cart_item.quantity

            order_items.append(
                OrderItem(
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price_at_purchase=current_price
                )
            )

        # 3. Создаем главный объект заказа
        new_order = Order(
            user_id=user_id,
            total_price=total_price,
            delivery_address=delivery_address,
            user_comment=user_comment,
            status="pending",
            items=order_items  # SQLAlchemy сама свяжет OrderItem с новым Order
        )
        self.session.add(new_order)

        # 4. Очищаем корзину пользователя
        stmt = delete(CartItem).where(CartItem.user_id == user_id)
        await self.session.execute(stmt)

        # 5. Фиксируем всю транзакцию
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
            .order_by(Order.created_at.desc())  # Свежие заказы сверху
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
                    Order.user_id == user_id  # Защита: чужой заказ посмотреть нельзя
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

