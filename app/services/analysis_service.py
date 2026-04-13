from typing import Optional
import re
import asyncio
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.session import AsyncSessionLocal
from app.services.github_service import github_service
from app.services.ai_service import ai_service
from app.repositories.analysis_repository import analysis_repository
from app.services.user_system_prompt_service import user_system_prompt_service
from app.schemas.analysis import AnalysisCreate, AnalysisReviewCreate, AnalysisUpdate
from app.models.analysis import Analysis, AnalysisReview
from app.models.user import User


class AnalysisService:
    @staticmethod
    def parse_github_pr_url(url: str) -> Dict[str, Any]:
        """Validates and extracts owner, repo, and pull number from a GitHub PR URL."""
        pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.match(pattern, url)
        if not match:
            raise HTTPException(
                status_code=400, detail="Invalid GitHub Pull Request URL."
            )

        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "pull_number": int(match.group(3)),
        }

    async def initiate_analysis(
        self, db: AsyncSession, user: User, pr_url: str
    ) -> Analysis:
        """Initializes the analysis record in the database."""
        pr_data = self.parse_github_pr_url(pr_url)
        analysis_in = AnalysisCreate(
            user_id=user.id,
            repo_owner=pr_data["owner"],
            repo_name=pr_data["repo"],
            pull_number=pr_data["pull_number"],
            status="in_progress",
        )
        return await analysis_repository.create(db, obj_in=analysis_in)

    async def perform_analysis_task(self, analysis_id: int, user: User, pr_url: str):
        """Background task to perform the full PR analysis."""
        async with AsyncSessionLocal() as db:
            try:
                # 1. Parse URL
                pr_data = self.parse_github_pr_url(pr_url)
                owner = pr_data["owner"]
                repo = pr_data["repo"]
                pull_number = pr_data["pull_number"]

                # 2. Fetch User System Prompt
                user_prompt_obj = await user_system_prompt_service.get_prompt(
                    db, user.id
                )
                system_prompt = (
                    user_prompt_obj.system_prompt if user_prompt_obj else None
                )

                # 3. Get Access Token
                access_token = await github_service.get_valid_access_token(db, user)
                if not access_token:
                    raise Exception("GitHub access token not found or invalid.")

                # 4. Fetch PR Files
                files = await github_service.get_pull_request_files(
                    access_token, owner, repo, pull_number
                )
                if not files:
                    raise Exception("No files found in this Pull Request.")

                # 5. Process Files and Patch Content
                analysis_tasks = []
                file_metadata = []

                for file in files:
                    filename = file.get("filename")
                    patch = file.get("patch")
                    if not patch:
                        continue
                    analysis_tasks.append(
                        ai_service.analyze_chunk(
                            filename, patch, system_prompt=system_prompt
                        )
                    )
                    file_metadata.append(filename)

                if not analysis_tasks:
                    raise Exception(
                        "No relevant code changes (patch data) found in PR."
                    )

                # 6. Run AI Analysis in parallel
                chunk_reviews = await asyncio.gather(*analysis_tasks)

                # 7. Aggregate results
                overall_review = await ai_service.aggregate_reviews(
                    chunk_reviews, system_prompt=system_prompt
                )

                # 8. Update Analysis in DB
                db_analysis = await analysis_repository.get(db, id=analysis_id)
                if not db_analysis:
                    return

                analysis_update = AnalysisUpdate(
                    overall_summary=overall_review["overall_summary"],
                    overall_risk_score=overall_review["overall_risk_score"],
                    final_recommendation=overall_review["final_recommendation"],
                    status="completed",
                )
                await analysis_repository.update(
                    db, db_obj=db_analysis, obj_in=analysis_update
                )

                # 9. Store Child Reviews
                for i, review in enumerate(chunk_reviews):
                    review_in = AnalysisReviewCreate(
                        analysis_id=db_analysis.id,
                        filename=file_metadata[i],
                        summary=review["summary"],
                        issues=review.get("issues", []),
                        risk_score=review["risk_score"],
                    )
                    await analysis_repository.create_review(db, obj_in=review_in)

            except Exception as e:
                db_analysis = await analysis_repository.get(db, id=analysis_id)
                if db_analysis:
                    await analysis_repository.update(
                        db,
                        db_obj=db_analysis,
                        obj_in=AnalysisUpdate(status="failed", error_message=str(e)),
                    )

    async def get_analysis_status(
        self, db: AsyncSession, analysis_id: int
    ) -> Optional[Analysis]:
        return await analysis_repository.get(db, id=analysis_id)

    async def update_notification_status(
        self, db: AsyncSession, analysis_id: int, is_notified: bool
    ) -> Optional[Analysis]:
        db_analysis = await analysis_repository.get(db, id=analysis_id)
        if not db_analysis:
            return None
        return await analysis_repository.update(
            db, db_obj=db_analysis, obj_in={"is_notified": is_notified}
        )

    async def get_user_history(
        self, db: AsyncSession, user_id: int, pr_url: Optional[str] = None
    ) -> List[Analysis]:
        """Retrieves the history of analyses for a given user, optionally filtered by PR URL."""
        if pr_url:
            pr_data = self.parse_github_pr_url(pr_url)
            return await analysis_repository.get_user_history_by_pr(
                db,
                user_id=user_id,
                owner=pr_data["owner"],
                repo=pr_data["repo"],
                pull_number=pr_data["pull_number"],
            )
        return await analysis_repository.get_user_history(db, user_id=user_id)

    async def get_reviews(
        self, db: AsyncSession, analysis_id: int
    ) -> List[AnalysisReview]:
        """Retrieves all reviews for a specific analysis."""
        return await analysis_repository.get_reviews(db, analysis_id=analysis_id)


analysis_service = AnalysisService()
