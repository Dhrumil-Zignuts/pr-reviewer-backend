from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routes import auth, users, diag, analysis, prompts
from app.exceptions.handlers import (
    AppException,
    app_exception_handler,
    global_exception_handler,
)
from app.middleware.logging import LoggingMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_middleware(LoggingMiddleware)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(diag.router, prefix=f"{settings.API_V1_STR}/diag", tags=["diag"])
app.include_router(
    analysis.router, prefix=f"{settings.API_V1_STR}/analysis", tags=["analysis"]
)
app.include_router(
    prompts.router, prefix=f"{settings.API_V1_STR}/prompts", tags=["prompts"]
)


@app.get("/")
async def root():
    return {"message": "Welcome to PR Reviewer API"}
