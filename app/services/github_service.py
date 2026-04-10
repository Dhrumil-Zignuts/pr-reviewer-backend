import httpx
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.schemas.auth import GitHubUser
from app.models.user import User
from app.repositories.user_repository import user_repository

logger = logging.getLogger(__name__)


class GitHubService:
    def __init__(self):
        # Initialize a shared client to reuse connections
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0, connect=30.0),
            headers={"Accept": "application/json"},
        )

    async def get_access_token(self, code: str) -> dict:
        try:
            logger.info(f"DEBUG: Attempting to exchange code for token at GitHub...")
            response = await self._client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.FRONTEND_BASE_URL,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.ConnectTimeout:
            logger.error("Connection to GitHub timed out. Retrying once...")
            # Simple retry for transient network issues
            response = await self._client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.FRONTEND_BASE_URL,
                },
            )
            return response.json()
        except Exception as e:
            logger.error(f"GitHub OAuth Error: {str(e)}")
            raise

    async def refresh_access_token(self, refresh_token: str) -> dict:
        response = await self._client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        return response.json()

    async def get_valid_access_token(self, db: AsyncSession, user: User) -> str:
        is_expired = False
        now = datetime.now(timezone.utc)

        if user.github_token_expires_at:
            expires_at = user.github_token_expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            is_expired = now + timedelta(minutes=5) >= expires_at

        if (is_expired or not user.github_access_token) and user.github_refresh_token:
            token_data = await self.refresh_access_token(user.github_refresh_token)

            access_token = token_data.get("access_token")
            new_refresh_token = (
                token_data.get("refresh_token") or user.github_refresh_token
            )
            expires_in = token_data.get("expires_in")

            update_data = {
                "github_access_token": access_token,
                "github_refresh_token": new_refresh_token,
            }
            if expires_in:
                update_data["github_token_expires_at"] = now + timedelta(
                    seconds=expires_in
                )

            await user_repository.update(db, db_obj=user, obj_in=update_data)
            return access_token

        return user.github_access_token

    async def get_user_profile(self, access_token: str) -> GitHubUser:
        response = await self._client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {access_token}"},
        )
        data = response.json()
        return GitHubUser(**data)


github_service = GitHubService()
