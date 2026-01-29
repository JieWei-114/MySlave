from datetime import date

import httpx

from app.config.settings import settings
from app.core.db import tavily_quota_collection

MAX_EXTRACT_LENGTH = settings.TAVILY_EXTRACT_MAX_LENGTH


def consume_tavily():
    today = date.today()
    month_key = f'{today.year}-{today.month:02d}'

    tavily_quota_collection.update_one(
        {'month': month_key},
        {'$inc': {'count': 1}},
        upsert=True,
    )


async def extract_url(url: str) -> str:
    # Extract main content from a URL using Tavily's extract API

    print('Tavily extract LOADED')
    print(f'Tavily extract CALLED with {url}')

    if not settings.TAVILY_API_KEY:
        print('Tavily missing api key')
        return ''

    timeout = httpx.Timeout(settings.TAVILY_EXTRACT_TIMEOUT)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(
                f'{settings.TAVILY_URL}/extract',
                json={
                    'api_key': settings.TAVILY_API_KEY,
                    'urls': [url],
                    'include_images': False,
                },
            )
            res.raise_for_status()
    except Exception as e:
        print('Tavily extract ERROR:', type(e).__name__, e)
        return ''

    try:
        data = res.json()
        results = data.get('results', [])

        if not results:
            print('Tavily extract empty results')
            return ''

        item = results[0]

        content = item.get('content') or item.get('raw_content') or ''

        if not content.strip():
            print('Tavily no extractable content')
            return ''

        consume_tavily()
        print('Tavily quota decremented')

        if len(content) > MAX_EXTRACT_LENGTH:
            return content[:MAX_EXTRACT_LENGTH].rstrip() + '…'

        return content

    except Exception as e:
        print('Tavily extract ERROR', type(e).__name__, e)
        return ''
