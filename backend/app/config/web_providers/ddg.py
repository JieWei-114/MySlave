from duckduckgo_search import DDGS
from app.config.web_providers.base import WebSearchProvider

class DuckDuckGoProvider(WebSearchProvider):
    name = "ddg"

    async def search(self, query: str, limit: int = 5):
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=limit))

        return [
            {
                "title": r.get("title"),
                "snippet": r.get("body"),
                "link": r.get("href"),
                "source": "ddg",
            }
            for r in results
        ]
