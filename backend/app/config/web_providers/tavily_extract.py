import httpx

from app.config.settings import settings

MAX_EXTRACT_LENGTH = 10_000


async def extract_url(url: str) -> str:
    """Extract main content from a URL using Tavily's extract API."""

    if not settings.TAVILY_API_KEY:
        return ''

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
            res = await client.post(
                'https://api.tavily.com/extract',
                json={
                    'api_key': settings.TAVILY_API_KEY,
                    'urls': [url],
                    'include_images': False,
                },
            )
            res.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException):
        return ''

    try:
        data = res.json()
        results = data.get('results', [])
        if not results:
            return ''

        content = results[0].get('content', '')
        if len(content) > MAX_EXTRACT_LENGTH:
            return content[:MAX_EXTRACT_LENGTH].rstrip() + '…'
        return content
    except (KeyError, IndexError, Exception):
        return ''
