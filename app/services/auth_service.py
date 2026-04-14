from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate
from app.schemas.auth import GitHubUser
from app.core import security


class AuthService:
    async def authenticate_github_user(
        self, db: AsyncSession, github_user: GitHubUser, token_data: dict
    ) -> str:
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")

        expires_at = None
        if expires_in:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        user = await user_repository.get_by_github_id(db, github_id=github_user.id)

        token_fields = {
            "github_access_token": access_token,
            "github_refresh_token": refresh_token,
            "github_token_expires_at": expires_at,
        }

        if not user:
            # Check if user exists by email if available
            if github_user.email:
                user = await user_repository.get_by_email(db, email=github_user.email)

            if user:
                # Update existing user with GitHub ID and tokens
                update_data = {"github_id": github_user.id, **token_fields}
                user = await user_repository.update(db, db_obj=user, obj_in=update_data)
            else:
                # Create new user
                user_in = UserCreate(
                    username=github_user.login,
                    email=github_user.email,
                    github_id=github_user.id,
                    avatar_url=github_user.avatar_url,
                    **token_fields
                )
                user = await user_repository.create(db, obj_in=user_in)
        else:
            # Update profile info and tokens
            update_data = {
                "username": github_user.login,
                "avatar_url": github_user.avatar_url,
                **token_fields,
            }
            user = await user_repository.update(db, db_obj=user, obj_in=update_data)

        # Generate JWT Access Token
        jwt_token = security.create_access_token(user.id)

        # Store the issued JWT back to the database
        await user_repository.update(
            db, db_obj=user, obj_in={"jwt_access_token": jwt_token}
        )

        return jwt_token

    async def logout(self, db: AsyncSession, user_id: int):
        """Invalidates the current session by clearing the stored JWT token."""
        user = await user_repository.get(db, id=user_id)
        if user:
            await user_repository.update(
                db, db_obj=user, obj_in={"jwt_access_token": None}
            )


auth_service = AuthService()
