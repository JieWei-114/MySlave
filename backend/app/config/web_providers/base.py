from abc import ABC, abstractmethod
from typing import Any


class WebSearchProvider(ABC):
    """
    Abstract base for all web search providers.
    Each provider must implement search() and define a name.
    """

    name: str

    @abstractmethod
    async def search(self, query: str, limit: int = None) -> list[dict[str, Any]]:
        """
        Search for query and return list of results.

        Args:
            query: The search query string
            limit: Maximum number of results to return

        Returns:
            List of dicts with keys: title, snippet, link, source
        """
        pass
