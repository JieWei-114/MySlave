import httpx
from datetime import date
from app.config.settings import settings
from app.core.db import db
from app.config.web_providers.base import WebSearchProvider

quota = db["tavily_quota"]

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

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        if not settings.TAVILY_API_KEY:
            raise Exception("TAVILY_API_KEY_NOT_SET")

        if remaining_tavily_quota() <= 0:
            raise Exception("TAVILY_MONTHLY_QUOTA_EXCEEDED")

        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.TAVILY_API_KEY,
                    "query": query,
                    "max_results": limit,
                    "search_depth": "advanced",
                },
            )

        consume_tavily()

        data = res.json().get("results", [])
        return [
            {
                "title": r.get("title"),
                "snippet": r.get("content"),
                "link": r.get("url"),
                "source": "tavily",
            }
            for r in data
        ]