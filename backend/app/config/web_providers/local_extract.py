from __future__ import annotations

import asyncio
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from readability import Document

# Hard guards
MAX_CHARS = 10_000  # Cap returned text length
MAX_BYTES = 10_000_000  # Cap download size (~10 MB)
REQUEST_TIMEOUT = 20.0  # Seconds for connect+read

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
)

ALLOWED_CONTENT_TYPES = ('text/html', 'application/xhtml+xml')

async def _fetch_html(url: str) -> Optional[str]:
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
        # 'Referer': 'https://www.google.com/',
        # 'Accept-Encoding': 'identity',
    }

    timeout = httpx.Timeout(20.0)

    async with httpx.AsyncClient(
        follow_redirects=True,
        headers=headers,
        timeout=timeout,
    ) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()

            ctype = resp.headers.get('content-type', '').lower()
            if not any(t in ctype for t in ALLOWED_CONTENT_TYPES):
                return None

            if not resp.text.strip():
                print('[fetch_html] empty body returned')
                return None

            return resp.text
        except Exception as e:
            print('[fetch_html ERROR]', type(e).__name__, e)
            return None

def _extract_main_text(html: str) -> str:
    doc = Document(html)
    clean_html = doc.summary(html_partial=True)

    soup = BeautifulSoup(clean_html, 'lxml')
    text = soup.get_text('\n')

    # Collapse excessive blank lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return '\n'.join(lines).strip()

async def extract_wikipedia(url: str) -> str:
    """
    Wikipedia-specific extractor (bypass Readability)
    """

    try:
        content = None 
        html = await _fetch_html(url)
        if not html:
            print('[wiki] html fetch failed')
            return ''

        soup = BeautifulSoup(html, 'lxml')

        content = (
            soup.select_one('#mw-content-text .mw-parser-output') \
            or soup.select_one('.mw-parser-output')
        )

        print('[wiki] content found:', content is not None)

        if not content:
            return ''

        # Remove tables, infoboxes, navboxes
        # for tag in content.find_all(['table', 'sup', 'style', 'script']):
        #     tag.decompose()

        paragraphs = [
            p.get_text(' ', strip=True) for p in content.find_all('p') if p.get_text(strip=True)
        ]

        print('[wiki] p count:', len(content.find_all('p')))
        print('[wiki] extracted paragraphs:', len(paragraphs))

        text = '\n\n'.join(paragraphs)

        if not text.strip():
            print('[wiki] fallback to container text')
            text = content.get_text('\n', strip=True)

        return text.strip()[:MAX_CHARS]

    except Exception as e:
        print('[extract_wikipedia ERROR]', e)
        return ''


async def extract_url_local(url: str) -> str:
    """Download and extract main text from a URL with safety limits."""

    print('local_extract.py LOADED')
    print(f'extract_url_local CALLED with {url}')

    if 'wikipedia.org' in url:
        return await extract_wikipedia(url)

    try:
        html = await _fetch_html(url)
        if not html:
            return ''

        text = await asyncio.to_thread(_extract_main_text, html)
    except Exception:
        return ''

    if not text:
        return ''

    if len(text) > MAX_CHARS:
        return text[:MAX_CHARS].rstrip() + '…'

    return text
