from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None


class GitHubUser(BaseModel):
    id: int
    login: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
