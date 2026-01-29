import httpx
from app.config.settings import settings

MAX_EXTRACT_LENGTH = 40_000


async def extract_url(url: str) -> str:
    """Extract main content from a URL using Tavily's extract API."""

    print('tavily_extract.py LOADED')
    print(f'Tavily extract CALLED with {url}')

    if not settings.TAVILY_API_KEY:
        print('[tavily] missing api key')
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
    except Exception as e:
        print('[tavily HTTP ERROR]', type(e).__name__, e)
        return ''

    try:
        data = res.json()
        results = data.get('results', [])

        if not results:
            print('[tavily] empty results')
            return ''

        item = results[0]

        content = (
            item.get('content')
            or item.get('raw_content')
            or ''
        )

        if not content.strip():
            print('[tavily] no extractable content')
            return ''

        if len(content) > MAX_EXTRACT_LENGTH:
            return content[:MAX_EXTRACT_LENGTH].rstrip() + '…'

        return content

    except Exception as e:
        print('[tavily PARSE ERROR]', type(e).__name__, e)
        return ''
