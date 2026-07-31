from sqlalchemy import select

from database.models.category import Category
from utils.logger import logger


class ShopCategoriesMixin:

    async def get_category_by_id(self, category_id: int) -> Category | None:
        logger.info(f"Fetching shop category id={category_id}")
        query = select(Category).where(Category.id == category_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_categories_by_parent(self, parent_id: int | None = None) -> list:
        logger.info(f"Fetching shop categories by parent_id={parent_id}")
        query = select(Category).where(Category.parent_id == parent_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())