import logging
import json
import asyncio
from google import genai
from google.genai import types
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


from app.services.ai_base import BaseAIService


class GeminiService(BaseAIService):
    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model_id = settings.GEMINI_MODEL
        else:
            logger.warning("GEMINI_API_KEY is not set. Gemini Features will not work.")
            self.client = None

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 15000) -> List[str]:
        """Splits text into manageable chunks for Gemini."""
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    async def analyze_chunk(
        self, filename: str, patch: str, system_prompt: str = None, retries: int = 3
    ) -> Dict[str, Any]:
        """Analyzes a single chunk of code diff using Gemini AI with retries."""
        if not self.client:
            return self._mock_review(filename)

        custom_instructions = (
            f"\nCustom Instructions: {system_prompt}\n" if system_prompt else ""
        )
        prompt = f"""
        You are an expert code reviewer. {custom_instructions}Analyze the following code diff for the file '{filename}'.
        
        Analyze the code for:
        1. Summary of changes.
        2. Potential bugs or logic errors.
        3. Code quality and best practices issues.
        4. Security concerns (vulnerabilities, hardcoded secrets, etc.).
        5. A risk score from 0.0 to 10.0 (where 10.0 is highest risk).

        Return the response EXACTLY as a JSON object with the following keys:
        - "summary": (string)
        - "issues": (list of objects) Each object must have:
            - "description": (string) A clear description of the issue.
            - "snippet": (string) The corresponding problematic code snippet.
        - "risk_score": (float) A risk score from 0.0 to 10.0.

        Focus specifically on:
        - Missing unique constraints.
        - Incorrect or inefficient relationships.
        - Inconsistent naming conventions for tables and keys.
        - Redundant or missing indexing.

        Diff content:
        {patch}
        """

        for attempt in range(retries):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    ),
                )
                return json.loads(response.text)
            except Exception as e:
                logger.error(
                    f"Error calling Gemini API for {filename} (attempt {attempt + 1}/{retries}): {str(e)}"
                )
                if attempt == retries - 1:
                    return self._mock_review(filename, error=str(e))
                await asyncio.sleep(2**attempt)  # Exponential backoff

    async def aggregate_reviews(
        self,
        chunk_reviews: List[Dict[str, Any]],
        system_prompt: str = None,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """Generates a final overall review from all chunks using Gemini AI with retries."""
        if not self.client or not chunk_reviews:
            return self._mock_aggregation(chunk_reviews)

        reviews_json = json.dumps(chunk_reviews, indent=2)
        custom_instructions = (
            f"\nCustom Instructions: {system_prompt}\n" if system_prompt else ""
        )
        prompt = f"""
        You are a lead developer. {custom_instructions}Below are individual code reviews for files in a Pull Request.
        Review the collective findings and provide an overall assessment.

        Provide:
        1. Overall summary of the whole PR.
        2. Summary of high-risk issues found across all files.
        3. A final overall risk score (0.0 to 10.0).
        4. A final recommendation: "Approve" or "Request Changes".

        Return the response EXACTLY as a JSON object with the following keys:
        - "overall_summary": (string)
        - "high_risk_issues": (string)
        - "overall_risk_score": (float)
        - "final_recommendation": (string: "Approve" or "Request Changes")

        Individual Reviews:
        {reviews_json}
        """

        for attempt in range(retries):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    ),
                )
                return json.loads(response.text)
            except Exception as e:
                logger.error(
                    f"Error calling Gemini API for aggregation (attempt {attempt + 1}/{retries}): {str(e)}"
                )
                if attempt == retries - 1:
                    return self._mock_aggregation(chunk_reviews)
                await asyncio.sleep(2**attempt)  # Exponential backoff

    def _mock_review(self, filename: str, error: str = None) -> Dict[str, Any]:
        """Fallback mock if API fails or key is missing."""
        return {
            "summary": f"Review for {filename} (Fallback)",
            "issues": [
                {"description": f"Fallback issue for {filename}", "snippet": "N/A"}
            ],
            "risk_score": 0.0,
        }

    def _mock_aggregation(self, chunk_reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback mock for aggregation."""
        avg_risk = (
            sum(r.get("risk_score", 0) for r in chunk_reviews) / len(chunk_reviews)
            if chunk_reviews
            else 0
        )
        return {
            "overall_summary": "Overall summary (Fallback)",
            "high_risk_issues": "None (Fallback)",
            "overall_risk_score": avg_risk,
            "final_recommendation": "Approve" if avg_risk < 5 else "Request Changes",
        }
