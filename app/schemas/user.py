from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    username: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    username: str
    github_id: Optional[int] = None
    github_access_token: Optional[str] = None
    github_refresh_token: Optional[str] = None
    github_token_expires_at: Optional[datetime] = None
    jwt_access_token: Optional[str] = None


class UserUpdate(UserBase):
    github_access_token: Optional[str] = None
    github_refresh_token: Optional[str] = None
    github_token_expires_at: Optional[datetime] = None
    jwt_access_token: Optional[str] = None


class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class User(UserInDBBase):
    pass
