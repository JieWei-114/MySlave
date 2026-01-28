from typing import Any
import httpx
from app.config.settings import settings
from app.core.db import serper_quota_collection
from app.config.web_providers.base import WebSearchProvider

quota = serper_quota_collection

def remaining_serper_quota() -> int:
    doc = quota.find_one({"_id": "serper"})
    if not doc:
        return settings.SERPER_TOTAL_LIMIT
    return max(0, settings.SERPER_TOTAL_LIMIT - doc["count"])

def consume_serper():
    quota.update_one(
        {"_id": "serper"},
        {"$inc": {"count": 1}},
        upsert=True,
    )

class SerperProvider(WebSearchProvider):
    name = "serper"

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not settings.SERPER_API_KEY:
            return []

        if remaining_serper_quota() <= 0:
            return []

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                res = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": settings.SERPER_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={"q": query, "num": limit},
                )
                res.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException):
            return []

        try:
            data = res.json()
        except Exception:
            return []

        results = data.get("organic", [])
        if not results:
            return []

        consume_serper()

        return [
            {
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "link": r.get("link", ""),
                "source": "serper",
            }
            for r in results
            if r.get("link")
        ]