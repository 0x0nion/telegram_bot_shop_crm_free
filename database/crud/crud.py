from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database.models.category import Category
from database.models.product import Product

# --- READ (Получение с учетом вложенности) ---

async def get_categories_by_parent(session: AsyncSession, parent_id: int | None = None):
    """
    Получает категории для текущего уровня.
    Если parent_id=None — отдаст корневые.
    Если передан ID — отдаст подкатегории для этой категории.
    """
    result = await session.execute(
        select(Category).where(Category.parent_id == parent_id)
    )
    return result.scalars().all()

async def get_items_by_category(session: AsyncSession, category_id: int):
    """Получает товары, привязанные к конкретной подкатегории"""
    result = await session.execute(
        select(Product).where(Product.category_id == category_id)
    )
    return result.scalars().all()

async def get_category_by_id(session: AsyncSession, category_id: int):
    """Нужно, чтобы получить имя текущей категории для заголовка"""
    result = await session.execute(
        select(Category).where(Category.id == category_id)
    )
    return result.scalar_one_or_none()