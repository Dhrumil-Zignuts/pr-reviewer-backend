from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        query = select(self.model).where(self.model.email == email)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_github_id(
        self, db: AsyncSession, *, github_id: int
    ) -> Optional[User]:
        query = select(self.model).where(self.model.github_id == github_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_by_username(
        self, db: AsyncSession, *, username: str
    ) -> Optional[User]:
        query = select(self.model).where(self.model.username == username)
        result = await db.execute(query)
        return result.scalars().first()


user_repository = UserRepository(User)
