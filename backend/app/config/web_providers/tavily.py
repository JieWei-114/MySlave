import httpx
from datetime import date
from typing import Any
from app.config.settings import settings
from app.core.db import tavily_quota_collection
from app.config.web_providers.base import WebSearchProvider

quota = tavily_quota_collection

def _month_key():
    today = date.today()
    return f"{today.year}-{today.month:02d}"

def remaining_tavily_quota() -> int:
    doc = quota.find_one({"month": _month_key()})
    if not doc:
        return settings.TAVILY_MONTHLY_LIMIT
    return max(0, settings.TAVILY_MONTHLY_LIMIT - doc["count"])

def consume_tavily():
    quota.update_one(
        {"month": _month_key()},
        {"$inc": {"count": 1}},
        upsert=True,
    )

class TavilyProvider(WebSearchProvider):
    name = "tavily"

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not settings.TAVILY_API_KEY:
            return []

        if remaining_tavily_quota() <= 0:
            return []

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
                res = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": settings.TAVILY_API_KEY,
                        "query": query,
                        "max_results": limit,
                        "search_depth": "advanced",
                        "include_answer": False,
                        "include_images": False,
                    },
                )
                res.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException):
            return []

        try:
            data = res.json()
        except Exception:
            return []

        results = data.get("results", [])
        if not results:
            return []

        consume_tavily()

        return [
            {
                "title": r.get("title", ""),
                "snippet": r.get("content", ""),
                "link": r.get("url", ""),
                "source": "tavily",
            }
            for r in results
            if r.get("url")
        ]