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

    async def create_reviews(
        self, db: AsyncSession, *, objs_in: List[AnalysisReviewCreate]
    ) -> List[AnalysisReview]:
        db_objs = [AnalysisReview(**obj_in.model_dump()) for obj_in in objs_in]
        db.add_all(db_objs)
        await db.commit()
        return db_objs

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

    async def get_user_history_by_repo(
        self, db: AsyncSession, *, user_id: int, owner: str, repo: str
    ) -> List[Analysis]:
        from sqlalchemy import select

        query = (
            select(Analysis)
            .where(
                Analysis.user_id == user_id,
                Analysis.repo_owner == owner,
                Analysis.repo_name == repo,
            )
            .order_by(Analysis.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def get_user_history_grouped(
        self, db: AsyncSession, *, user_id: int
    ) -> List[dict]:
        from sqlalchemy import select, func, desc, text

        # Using PostgreSQL window function for efficient aggregation and latest record retrieval
        # COUNT(*) OVER(PARTITION BY ...) gives us the count for each group
        # DISTINCT ON (repo_owner, repo_name, pull_number) combined with ORDER BY created_at DESC
        # gives us the latest record for each group.

        query = text(
            """
            SELECT DISTINCT ON (repo_owner, repo_name, pull_number)
                repo_owner,
                repo_name,
                pull_number,
                created_at as last_analysis_at,
                COUNT(*) OVER (PARTITION BY repo_owner, repo_name, pull_number) as analysis_count,
                status as latest_status,
                overall_risk_score as latest_risk_score,
                id as latest_analysis_id
            FROM analyses
            WHERE user_id = :user_id
            ORDER BY repo_owner, repo_name, pull_number, created_at DESC
        """
        )

        result = await db.execute(query, {"user_id": user_id})
        return [dict(row._mapping) for row in result]


analysis_repository = AnalysisRepository(Analysis)
