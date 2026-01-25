from abc import ABC, abstractmethod

class WebSearchProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, limit: int = 5) -> list[dict]:
        pass