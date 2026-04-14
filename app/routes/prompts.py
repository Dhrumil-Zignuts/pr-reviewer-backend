from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user_system_prompt import (
    UserSystemPromptBase,
    UserSystemPromptResponse,
)
from app.services.user_system_prompt_service import user_system_prompt_service

router = APIRouter()


@router.get("/system", response_model=UserSystemPromptResponse)
async def get_my_system_prompt(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prompt = await user_system_prompt_service.get_prompt(db, current_user.id)
    if not prompt:
        raise HTTPException(
            status_code=404, detail="System prompt not found for this user."
        )
    return prompt


@router.post("/system", response_model=UserSystemPromptResponse)
async def update_my_system_prompt(
    prompt_in: UserSystemPromptBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await user_system_prompt_service.update_prompt(
        db, current_user.id, prompt_in.system_prompt
    )
