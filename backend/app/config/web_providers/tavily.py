import logging
from datetime import date
from typing import Any

import httpx

from app.config.settings import settings
from app.config.web_providers.base import WebSearchProvider
from app.core.db import tavily_quota_collection

logger = logging.getLogger(__name__)

quota = tavily_quota_collection


def month_key():
    today = date.today()
    return f'{today.year}-{today.month:02d}'


def remaining_tavily_quota() -> int:
    doc = quota.find_one({'month': month_key()})
    if settings.TAVILY_MONTHLY_LIMIT is None:
        return 0
    if not doc:
        return settings.TAVILY_MONTHLY_LIMIT
    return max(0, settings.TAVILY_MONTHLY_LIMIT - doc['count'])


def consume_tavily():
    quota.update_one(
        {'month': month_key()},
        {'$inc': {'count': 1}},
        upsert=True,
    )


class TavilyProvider(WebSearchProvider):
    name = 'tavily'

    async def search(self, query: str, limit: int = None) -> list[dict[str, Any]]:
        if not settings.TAVILY_API_KEY:
            logger.warning('Tavily API key missing')
            return []

        if not settings.TAVILY_URL:
            logger.warning('Tavily URL missing')
            return []

        if limit is None:
            limit = settings.TAVILY_LIMIT

        if remaining_tavily_quota() <= 0:
            logger.info('Tavily quota exhausted')
            return []

        timeout = httpx.Timeout(settings.TAVILY_TIMEOUT)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.post(
                    f'{settings.TAVILY_URL}/search',
                    json={
                        'api_key': settings.TAVILY_API_KEY,
                        'query': query,
                        'max_results': limit,
                        'search_depth': 'advanced',
                        'include_answer': False,
                        'include_images': False,
                    },
                )
                res.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning('Tavily request failed: %s', e)
            return []

        try:
            data = res.json()
        except Exception as e:
            logger.warning('Tavily response parse failed: %s', e)
            return []

        results = data.get('results', [])
        if not results:
            return []

        consume_tavily()

        return [
            {
                'title': r.get('title', ''),
                'snippet': r.get('content', ''),
                'link': r.get('url', ''),
                'source': 'tavily',
            }
            for r in results
            if r.get('url')
        ]
