import asyncio
from typing import Any

from ddgs import DDGS

from app.config.web_providers.base import WebSearchProvider


class DuckDuckGoProvider(WebSearchProvider):
    name = 'ddg'

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        def _search():
            try:
                with DDGS(timeout=10) as ddgs:
                    return list(ddgs.text(query, max_results=limit))
            except Exception:
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
