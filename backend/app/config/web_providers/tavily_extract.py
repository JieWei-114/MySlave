from datetime import date

import httpx

from app.config.settings import settings
from app.core.db import tavily_quota_collection

import logging

logger = logging.getLogger(__name__)

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
    logger.info('Tavily extract called for %s', url)

    if not settings.TAVILY_API_KEY:
        logger.warning('Tavily extract missing API key')
        return ''
    
    if not settings.TAVILY_URL:
        logger.warning('Tavily extract missing URL')
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
        logger.warning('Tavily extract request failed: %s', e)
        return ''

    try:
        data = res.json()
        results = data.get('results', [])

        if not results:
            logger.info('Tavily extract returned no results')
            return ''

        item = results[0]

        content = item.get('content') or item.get('raw_content') or ''

        if not content.strip():
            logger.info('Tavily extract returned empty content')
            return ''

        consume_tavily()
        logger.info('Tavily quota decremented')

        if len(content) > MAX_EXTRACT_LENGTH:
            return content[:MAX_EXTRACT_LENGTH].rstrip() + '…'

        return content

    except Exception as e:
        logger.warning('Tavily extract parse error: %s', e)
        return ''
    