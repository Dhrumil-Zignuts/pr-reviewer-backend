from typing import Optional
import re
import logging
import asyncio
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.github_service import github_service
from app.services.ai_service import ai_service
from app.repositories.analysis_repository import analysis_repository
from app.services.user_system_prompt_service import user_system_prompt_service
from app.schemas.analysis import AnalysisCreate, AnalysisReviewCreate, AnalysisUpdate
from app.models.analysis import Analysis, AnalysisReview
from app.models.user import User

logger = logging.getLogger(__name__)


class AnalysisService:
    @staticmethod
    def parse_github_url(url: str) -> Dict[str, Any]:
        """Parses a GitHub URL and extracts repo components or PR components."""
        # Check for PR URL first (more specific)
        pr_pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        pr_match = re.match(pr_pattern, url)
        if pr_match:
            return {
                "type": "pr",
                "owner": pr_match.group(1),
                "repo": pr_match.group(2),
                "pull_number": int(pr_match.group(3)),
            }

        # Check for Repo URL
        repo_pattern = r"https://github\.com/([^/]+)/([^/]+)"
        repo_match = re.match(repo_pattern, url)
        if repo_match:
            return {
                "type": "repo",
                "owner": repo_match.group(1),
                "repo": repo_match.group(2),
            }

        raise HTTPException(status_code=400, detail="Invalid GitHub URL.")

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
            status="pending",
        )
        return await analysis_repository.create(db, obj_in=analysis_in)

    async def perform_analysis_task(self, analysis_id: int, user_id: int, pr_url: str):
        """Background task to perform the full PR analysis with batch processing."""
        async with AsyncSessionLocal() as db:
            try:
                # 0. Set status to in_progress
                db_analysis = await analysis_repository.get(db, id=analysis_id)
                if db_analysis:
                    await analysis_repository.update(
                        db, db_obj=db_analysis, obj_in={"status": "in_progress"}
                    )

                # 1. Fetch User and Parse URL
                from app.repositories.user_repository import user_repository

                user = await user_repository.get(db, id=user_id)
                if not user:
                    logger.error(f"User {user_id} not found for analysis {analysis_id}")
                    return

                pr_data = self.parse_github_url(pr_url)
                owner = pr_data["owner"]
                repo = pr_data["repo"]
                pull_number = pr_data.get("pull_number")

                if not pull_number:
                    raise Exception("Analysis requires a Pull Request URL.")

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

                # 5. Filter files with patches
                all_chunks = []
                for file in files:
                    filename = file.get("filename")
                    patch = file.get("patch")
                    if patch:
                        all_chunks.append({"filename": filename, "patch": patch})

                if not all_chunks:
                    raise Exception(
                        "No relevant code changes (patch data) found in PR."
                    )

                # 6. Process in batches
                chunk_reviews = []
                batch_size = settings.AI_BATCH_SIZE

                for i in range(0, len(all_chunks), batch_size):
                    batch = all_chunks[i : i + batch_size]
                    batch_tasks = [
                        ai_service.analyze_chunk(
                            item["filename"], item["patch"], system_prompt=system_prompt
                        )
                        for item in batch
                    ]
                    # Process current batch in parallel
                    batch_results = await asyncio.gather(*batch_tasks)
                    chunk_reviews.extend(batch_results)

                    # Yield control back to the event loop between batches
                    # to prevent blocking other concurrent API requests.
                    await asyncio.sleep(0)

                # 7. Aggregate results
                overall_review = await ai_service.aggregate_reviews(
                    chunk_reviews, system_prompt=system_prompt
                )

                # 8. Update Analysis in DB
                db_analysis = await analysis_repository.get(db, id=analysis_id)
                if not db_analysis:
                    return

                analysis_update = AnalysisUpdate(
                    overall_summary=overall_review.get(
                        "overall_summary", "No summary provided."
                    ),
                    overall_risk_score=overall_review.get("overall_risk_score", 0.0),
                    final_recommendation=overall_review.get(
                        "final_recommendation", "N/A"
                    ),
                    status="completed",
                )
                await analysis_repository.update(
                    db, db_obj=db_analysis, obj_in=analysis_update
                )

                # 9. Store Child Reviews
                reviews_in = []
                for i, review in enumerate(chunk_reviews):
                    raw_issues = review.get("issues", [])
                    sanitized_issues = []
                    if isinstance(raw_issues, list):
                        for issue in raw_issues:
                            if isinstance(issue, dict):
                                sanitized_issues.append(issue)
                            elif isinstance(issue, str):
                                sanitized_issues.append(
                                    {"description": issue, "snippet": ""}
                                )

                    reviews_in.append(
                        AnalysisReviewCreate(
                            analysis_id=db_analysis.id,
                            filename=all_chunks[i]["filename"],
                            summary=review.get("summary", "No summary provided."),
                            issues=sanitized_issues,
                            risk_score=review.get("risk_score", 0.0),
                        )
                    )
                await analysis_repository.create_reviews(db, objs_in=reviews_in)

            except Exception as e:
                logger.error(f"Analysis {analysis_id} failed: {str(e)}")
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
        self, db: AsyncSession, user_id: int, url: Optional[str] = None
    ) -> List[Any]:
        """Retrieves history, optionally grouped or filtered by Repo/PR URL."""
        if not url:
            return await analysis_repository.get_user_history_grouped(
                db, user_id=user_id
            )

        url_data = self.parse_github_url(url)
        if url_data["type"] == "pr":
            return await analysis_repository.get_user_history_by_pr(
                db,
                user_id=user_id,
                owner=url_data["owner"],
                repo=url_data["repo"],
                pull_number=url_data["pull_number"],
            )
        else:  # repo
            return await analysis_repository.get_user_history_by_repo(
                db, user_id=user_id, owner=url_data["owner"], repo=url_data["repo"]
            )

    async def get_reviews(
        self, db: AsyncSession, analysis_id: int
    ) -> List[AnalysisReview]:
        """Retrieves all reviews for a specific analysis."""
        return await analysis_repository.get_reviews(db, analysis_id=analysis_id)


analysis_service = AnalysisService()
