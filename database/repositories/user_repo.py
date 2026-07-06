# database/repositories/user_repo.py
from sqlalchemy import select
from database.repositories.base_repo import BaseRepository
from database.models.user import User

class UserRepository(BaseRepository):
    # --- Методы для работы с Пользователями ---

    async def get_user(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, user_id: int, username: str | None) -> User:
        user = User(id=user_id, username=username)
        self.session.add(user)
        await self.session.commit()
        return user

    async def update_language(self, user_id: int, language: str) -> None:
        user = await self.get_user(user_id)
        if user:
            user.language = language
            await self.session.commit()