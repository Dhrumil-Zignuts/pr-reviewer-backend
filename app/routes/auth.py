from app.middleware.logging import logger
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.github_service import github_service
from app.services.auth_service import auth_service
from app.core.config import settings
from app.schemas.auth import Token

router = APIRouter()


@router.get("/github/login")
async def github_login():
    # Use 'repo' scope to access repositories, commits, and pull requests.
    # Note: OAuth Apps use 'repo' for both public and private repository access.
    github_url = f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri={settings.FRONTEND_BASE_URL}&scope=repo,user:email"
    return RedirectResponse(github_url)


@router.get("/github/callback", response_model=Token)
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    token_data = await github_service.get_access_token(code)
    print("token_data", token_data)
    access_token = token_data.get("access_token")
    print("access_token", access_token)
    if not access_token:
        raise HTTPException(
            status_code=400, detail="Failed to retrieve access token from GitHub"
        )

    # Validate that required scopes were granted
    granted_scopes = token_data.get("scope", "").split(",")
    print("granted_scopes", granted_scopes)
    if "repo" not in granted_scopes:
        raise HTTPException(
            status_code=400,
            detail="Minimum required 'repo' scope (read access to repositories, commits, and PRs) was not granted",
        )

    github_user = await github_service.get_user_profile(access_token)
    print("github_user", github_user)
    jwt_token = await auth_service.authenticate_github_user(db, github_user, token_data)
    print("jwt_token", jwt_token)
    return {"access_token": jwt_token, "token_type": "bearer"}
