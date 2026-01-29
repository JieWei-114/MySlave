from typing import Any

import httpx

from app.config.settings import settings
from app.config.web_providers.base import WebSearchProvider


class SearXNGProvider(WebSearchProvider):
    name = 'searxng'

    async def search(self, query: str, limit: int = None) -> list[dict[str, Any]]:
        if not settings.SEARXNG_URL:
            return []

        if limit is None:
            limit = settings.SEARXNG_LIMIT

        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        timeout = httpx.Timeout(settings.SEARXNG_TIMEOUT)

        try:
            async with httpx.AsyncClient(headers=headers, timeout=timeout) as client:
                res = await client.get(
                    f'{settings.SEARXNG_URL}/search',
                    params={
                        'q': query,
                        'format': 'json',
                        'language': 'en',
                    },
                )
                res.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException):
            return []

        data = res.json().get('results', [])
        return [
            {
                'title': r.get('title', ''),
                'snippet': r.get('content', ''),
                'link': r.get('url', ''),
                'source': 'searxng',
            }
            for r in data[:limit]
            if r.get('url')
        ]
