from sqlalchemy import select
from database.repositories.base_repo import BaseRepository
from database.models.category import Category
from database.models.product import Product


class ShopRepository(BaseRepository):
    """Репозиторий для работы исключительно с витриной магазина (клиентская часть)"""

    async def get_category_by_id(self, category_id: int,) -> Category | None:
        query = select(Category).where(Category.id == category_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_categories_by_parent(self, parent_id: int | None = None) -> list:
        query = select(Category).where(Category.parent_id == parent_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_products_by_category(self, category_id: int | None) -> list[Product]:
        """Получить активные товары в категории"""
        result = await self.session.execute(
            select(Product).where(Product.category_id == category_id)
        )
        return list(result.scalars().all())

    async def get_product_by_id(self, product_id: int) -> Product | None:
        query = select(Product).where(Product.id == product_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_next_product(self, category_id: int, current_product_id: int) -> Product | None:
        """Получить следующий товар (с закольцовыванием)"""
        # 1. Ищем следующий по порядку
        query = select(Product).where(
            Product.category_id == category_id,
            Product.id > current_product_id
        ).order_by(Product.id.asc()).limit(1)

        result = await self.session.execute(query)
        next_prod = result.scalar_one_or_none()

        # 2. Если достигли конца списка, берем самый первый товар
        if not next_prod:
            query_first = select(Product).where(
                Product.category_id == category_id
            ).order_by(Product.id.asc()).limit(1)
            result_first = await self.session.execute(query_first)
            next_prod = result_first.scalar_one_or_none()

        return next_prod

    async def get_prev_product(self, category_id: int, current_product_id: int) -> Product | None:
        """Получить предыдущий товар (с закольцовыванием)"""
        # 1. Ищем предыдущий по порядку
        query = select(Product).where(
            Product.category_id == category_id,
            Product.id < current_product_id
        ).order_by(Product.id.desc()).limit(1)

        result = await self.session.execute(query)
        prev_prod = result.scalar_one_or_none()

        # 2. Если достигли начала списка, берем самый последний товар
        if not prev_prod:
            query_last = select(Product).where(
                Product.category_id == category_id
            ).order_by(Product.id.desc()).limit(1)
            result_last = await self.session.execute(query_last)
            prev_prod = result_last.scalar_one_or_none()

        return prev_prod