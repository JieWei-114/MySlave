import asyncio
import logging
from typing import Any

from ddgs import DDGS

from app.config.settings import settings
from app.config.web_providers.base import WebSearchProvider

logger = logging.getLogger(__name__)


class DuckDuckGoProvider(WebSearchProvider):
    name = 'ddg'

    async def search(self, query: str, limit: int = None) -> list[dict[str, Any]]:
        if limit is None:
            limit = settings.DDG_LIMIT

        timeout = settings.DDG_TIMEOUT

        def _search():
            try:
                with DDGS(timeout=timeout) as ddgs:
                    return list(ddgs.text(query, max_results=limit))
            except Exception as e:
                logger.warning('DDG search failed: %s', e)
                return []

        results = await asyncio.to_thread(_search)

        return [
            {
                'title': r.get('title', ''),
                'snippet': r.get('body', ''),
                'link': r.get('href', ''),
                'source': 'ddg',
            }
            for r in results
            if r.get('href')
        ]
    