import httpx
from datetime import date
from app.config.settings import settings
from app.core.db import db

quota = db['web_search_quota']

def _today():
    return date.today().isoformat()

def remaining_quota() -> int:
    doc = quota.find_one({'date': _today()})
    if not doc:
        return settings.WEB_SEARCH_DAILY_LIMIT
    return max(0, settings.WEB_SEARCH_DAILY_LIMIT - doc['count'])

def _consume():
    quota.update_one(
        {'date': _today()},
        {'$inc': {'count': 1}},
        upsert=True,
    )

async def web_search(query: str, limit: int = 5):
    if remaining_quota() <= 0:
        raise Exception('WEB_SEARCH_QUOTA_EXCEEDED')

    headers = {
        'X-API-KEY': settings.SERPER_API_KEY,
        'Content-Type': 'application/json',
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            'https://google.serper.dev/search',
            headers=headers,
            json={'q': query, 'num': limit},
        )

    _consume()

    data = res.json().get('organic', [])
    return [
        {
            'title': x.get('title'),
            'snippet': x.get('snippet'),
            'link': x.get('link'),
        }
        for x in data
    ]

async def maybe_web_search(query: str) -> list[dict]:
    keywords = ['latest', 'today', 'news', 'price', 'who is', 'what is']
    if any(k in query.lower() for k in keywords):
        return await web_search(query)
    return []
