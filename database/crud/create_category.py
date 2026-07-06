from sqlalchemy.ext.asyncio import AsyncSession
from database.models.category import Category  # Твоя модель категории

async def create_category(session: AsyncSession, name: str, parent_id: int | None = None):
    """Создает новую категорию (корневую или вложенную)"""
    new_category = Category(
        name=name,
        parent_id=parent_id
    )
    session.add(new_category)
    await session.commit()
    return new_category