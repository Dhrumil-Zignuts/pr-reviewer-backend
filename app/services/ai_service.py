import logging
from app.core.config import settings
from app.services.gemini_service import GeminiService
from app.services.openai_service import OpenAIService
from app.services.ai_base import BaseAIService

logger = logging.getLogger(__name__)


def get_ai_service() -> BaseAIService:
    """Factory function to get the configured AI service."""
    provider = settings.AI_PROVIDER.lower()

    if provider == "openai":
        logger.info("Using OpenAI Service")
        return OpenAIService()
    elif provider == "gemini":
        logger.info("Using Gemini Service")
        return GeminiService()
    else:
        logger.error(f"Unsupported AI provider: {provider}. Falling back to Gemini.")
        return GeminiService()


# Singleton instance
ai_service = get_ai_service()
