from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.models.user_system_prompt import UserSystemPrompt
from app.schemas.user_system_prompt import (
    UserSystemPromptCreate,
    UserSystemPromptUpdate,
)


class UserSystemPromptRepository(
    BaseRepository[UserSystemPrompt, UserSystemPromptCreate, UserSystemPromptUpdate]
):
    async def get_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> Optional[UserSystemPrompt]:
        query = select(UserSystemPrompt).where(UserSystemPrompt.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def upsert(
        self, db: AsyncSession, user_id: int, system_prompt: str
    ) -> UserSystemPrompt:
        db_obj = await self.get_by_user_id(db, user_id)
        if db_obj:
            db_obj.system_prompt = system_prompt
        else:
            db_obj = UserSystemPrompt(user_id=user_id, system_prompt=system_prompt)
            db.add(db_obj)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


user_system_prompt_repository = UserSystemPromptRepository(UserSystemPrompt)
