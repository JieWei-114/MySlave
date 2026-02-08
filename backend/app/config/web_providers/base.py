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

        """
        pass
