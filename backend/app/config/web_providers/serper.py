from datetime import date
import httpx
from app.config.settings import settings
from app.core.db import db
from app.config.web_providers.base import WebSearchProvider

quota = db["serper_quota"]

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

    async def search(self, query: str, limit: int = 5) -> list[dict]:
        if not settings.SERPER_API_KEY:
            raise Exception("SERPER_API_KEY_NOT_SET")

        if remaining_serper_quota() <= 0:
            raise Exception("SERPER_QUOTA_EXHAUSTED")

        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": settings.SERPER_API_KEY,
                    "Content-Type": "application/json",
                },
                json={"q": query, "num": limit},
            )

        consume_serper()

        data = res.json().get("organic", [])
        return [
            {
                "title": r.get("title"),
                "snippet": r.get("snippet"),
                "link": r.get("link"),
                "source": "serper",
            }
            for r in data
        ]
