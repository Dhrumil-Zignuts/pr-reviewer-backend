from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.models.analysis import Analysis, AnalysisReview
from app.schemas.analysis import AnalysisCreate, AnalysisUpdate, AnalysisReviewCreate


class AnalysisRepository(BaseRepository[Analysis, AnalysisCreate, AnalysisUpdate]):
    async def create_review(
        self, db: AsyncSession, *, obj_in: AnalysisReviewCreate
    ) -> AnalysisReview:
        obj_in_data = obj_in.model_dump()
        db_obj = AnalysisReview(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_reviews(
        self, db: AsyncSession, *, analysis_id: int
    ) -> List[AnalysisReview]:
        from sqlalchemy import select

        query = select(AnalysisReview).where(AnalysisReview.analysis_id == analysis_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_user_history(
        self, db: AsyncSession, *, user_id: int
    ) -> List[Analysis]:
        from sqlalchemy import select

        query = (
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_user_history_by_pr(
        self, db: AsyncSession, *, user_id: int, owner: str, repo: str, pull_number: int
    ) -> List[Analysis]:
        from sqlalchemy import select

        query = (
            select(Analysis)
            .where(
                Analysis.user_id == user_id,
                Analysis.repo_owner == owner,
                Analysis.repo_name == repo,
                Analysis.pull_number == pull_number,
            )
            .order_by(Analysis.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()


analysis_repository = AnalysisRepository(Analysis)
