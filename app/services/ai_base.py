from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseAIService(ABC):
    @abstractmethod
    async def analyze_chunk(
        self, filename: str, patch: str, system_prompt: str = None, retries: int = 3
    ) -> Dict[str, Any]:
        """Analyzes a single chunk of code diff."""
        pass

    @abstractmethod
    async def aggregate_reviews(
        self,
        chunk_reviews: List[Dict[str, Any]],
        system_prompt: str = None,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """Generates a final overall review from all chunks."""
        pass
