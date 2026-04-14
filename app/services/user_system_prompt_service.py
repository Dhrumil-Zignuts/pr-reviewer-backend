from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_system_prompt_repository import user_system_prompt_repository
from app.models.user_system_prompt import UserSystemPrompt
from app.schemas.user_system_prompt import UserSystemPromptCreate


class UserSystemPromptService:
    async def get_prompt(
        self, db: AsyncSession, user_id: int
    ) -> Optional[UserSystemPrompt]:
        return await user_system_prompt_repository.get_by_user_id(db, user_id)

    async def update_prompt(
        self, db: AsyncSession, user_id: int, system_prompt: str
    ) -> UserSystemPrompt:
        return await user_system_prompt_repository.upsert(db, user_id, system_prompt)


user_system_prompt_service = UserSystemPromptService()
