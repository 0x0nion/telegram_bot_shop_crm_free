from sqlalchemy import select
from database.models.product import Product
from database.repositories.base_repo import BaseRepository
from utils.logger import logger


class ShopProductsMixin:

    @property
    def _product_repo(self) -> BaseRepository[Product]:
        return BaseRepository(Product, self.session)

    async def get_products_by_category(self, category_id: int | None) -> list[Product]:
        """Получить активные товары в категории"""
        logger.info(f"Fetching shop products by category_id={category_id}")
        return await self._product_repo.get_all(Product.category_id == category_id)

    async def get_product_by_id(self, product_id: int) -> Product | None:
        logger.info(f"Fetching shop product id={product_id}")
        return await self._product_repo.get_by_id(product_id)

    async def get_next_product(self, category_id: int, current_product_id: int) -> Product | None:
        """Получить следующий товар (с закольцовыванием)"""
        logger.info(f"Fetching next product for category_id={category_id}, current_product_id={current_product_id}")

        products = await self._product_repo.get_all(
            Product.category_id == category_id,
            Product.id > current_product_id,
            order_by=Product.id.asc(),
            limit=1
        )
        if products:
            return products[0]

        # Закольцовывание на первый
        first_products = await self._product_repo.get_all(
            Product.category_id == category_id,
            order_by=Product.id.asc(),
            limit=1
        )
        return first_products[0] if first_products else None

    async def get_prev_product(self, category_id: int, current_product_id: int) -> Product | None:
        """Получить предыдущий товар (с закольцовыванием)"""
        logger.info(f"Fetching previous product for category_id={category_id}, current_product_id={current_product_id}")

        products = await self._product_repo.get_all(
            Product.category_id == category_id,
            Product.id < current_product_id,
            order_by=Product.id.desc(),
            limit=1
        )
        if products:
            return products[0]

        # Закольцовывание на последний
        last_products = await self._product_repo.get_all(
            Product.category_id == category_id,
            order_by=Product.id.desc(),
            limit=1
        )
        return last_products[0] if last_products else None