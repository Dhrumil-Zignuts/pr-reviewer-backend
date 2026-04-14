import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from typing import List, Union
from app.services.analysis_service import analysis_service
from app.schemas.analysis import (
    PRAnalysisRequest,
    AnalysisStatusResponse,
    AnalysisNotificationUpdate,
    AnalysisReviewResponse,
    AnalysisHistoryGrouped,
)

router = APIRouter()


@router.post("/analyze", response_model=AnalysisStatusResponse)
async def analyze_pr_endpoint(
    request: PRAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Initiate analysis record
    db_analysis = await analysis_service.initiate_analysis(
        db, current_user, str(request.pr_url)
    )

    # 2. Add background task using asyncio.create_task
    # This fires off the task immediately on the current event loop.
    asyncio.create_task(
        analysis_service.perform_analysis_task(
            db_analysis.id,
            current_user.id,
            str(request.pr_url),
        )
    )

    # 3. Return initial status
    return db_analysis


@router.get("/status/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status_endpoint(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_analysis = await analysis_service.get_analysis_status(db, analysis_id)
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return db_analysis


@router.patch("/notified/{analysis_id}", response_model=AnalysisStatusResponse)
async def update_notified_status_endpoint(
    analysis_id: int,
    request: AnalysisNotificationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_analysis = await analysis_service.update_notification_status(
        db, analysis_id, request.is_notified
    )
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return db_analysis


@router.get(
    "/history",
    response_model=Union[List[AnalysisStatusResponse], List[AnalysisHistoryGrouped]],
)
async def get_analysis_history_endpoint(
    pr_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves the analysis history for the current user, optionally filtered by repo/PR URL."""
    return await analysis_service.get_user_history(
        db, user_id=current_user.id, url=pr_url
    )


@router.get("/{analysis_id}/reviews", response_model=List[AnalysisReviewResponse])
async def get_analysis_reviews_endpoint(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves all reviews associated with a specific analysis."""
    # Check if analysis exists first (optional but good for 404)
    db_analysis = await analysis_service.get_analysis_status(db, analysis_id)
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    return await analysis_service.get_reviews(db, analysis_id=analysis_id)
