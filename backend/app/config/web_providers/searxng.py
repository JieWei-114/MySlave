import httpx

from app.config.settings import settings
from app.config.web_providers.base import WebSearchProvider

class SearXNGProvider(WebSearchProvider):
    name = "searxng"

    async def search(self, query: str, limit: int = 5):
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{settings.SEARXNG_URL}/search",
                params={
                    "q": query,
                    "format": "json",
                    "language": "en",
                },
            )

        data = res.json().get("results", [])
        return [
            {
                "title": r["title"],
                "snippet": r.get("content", ""),
                "link": r["url"],
                "source": "searxng",
            }
            for r in data[:limit]
        ]
