from database.models.category import Category
from database.repositories.base_repo import BaseRepository
from utils.logger import logger


class ShopCategoriesMixin:

    @property
    def _category_repo(self) -> BaseRepository[Category]:
        return BaseRepository(Category, self.session)

    async def get_category_by_id(self, category_id: int) -> Category | None:
        logger.info(f"Fetching shop category id={category_id}")
        return await self._category_repo.get_by_id(category_id)

    async def get_categories_by_parent(self, parent_id: int | None = None) -> list[Category]:
        logger.info(f"Fetching shop categories by parent_id={parent_id}")
        return await self._category_repo.get_all(Category.parent_id == parent_id)