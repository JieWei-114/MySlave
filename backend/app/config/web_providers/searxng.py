from typing import Any

import logging
import httpx

from app.config.settings import settings
from app.config.web_providers.base import WebSearchProvider

logger = logging.getLogger(__name__)

class SearXNGProvider(WebSearchProvider):
    name = 'searxng'

    async def search(self, query: str, limit: int = None) -> list[dict[str, Any]]:
        if not settings.SEARXNG_URL:
            return []

        if limit is None:
            limit = settings.SEARXNG_LIMIT

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        timeout = httpx.Timeout(settings.SEARXNG_TIMEOUT)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.get(
                    f'{settings.SEARXNG_URL}/search',
                    headers=headers,
                    params={
                        'q': query,
                        'format': 'json',
                        'language': 'en',
                    },
                )
                res.raise_for_status()
                payload = res.json()

        except Exception as e:
            logger.warning(f'SearXNG search failed: {e}')
            return []

        results = payload.get('results', [])

        return [
            {
                'title': r.get('title', ''),
                'snippet': r.get('content', ''),
                'link': r.get('url', ''),
                'source': 'searxng',
            }
            for r in results[:limit]
            if r.get('url')
        ]
