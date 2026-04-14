from pydantic import BaseModel
from typing import Optional


class UserSystemPromptBase(BaseModel):
    system_prompt: str


class UserSystemPromptCreate(UserSystemPromptBase):
    pass


class UserSystemPromptUpdate(UserSystemPromptBase):
    pass


class UserSystemPromptResponse(UserSystemPromptBase):
    user_id: int

    class Config:
        from_attributes = True
