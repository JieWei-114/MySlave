from __future__ import annotations

import asyncio
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from readability import Document


# Hard guards
MAX_CHARS = 10_000          # Cap returned text length
MAX_BYTES = 1_000_000       # Cap download size (~1 MB)
REQUEST_TIMEOUT = 8.0       # Seconds for connect+read

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

ALLOWED_CONTENT_TYPES = ("text/html", "application/xhtml+xml")


async def _fetch_html(url: str) -> Optional[str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }

    timeout = httpx.Timeout(REQUEST_TIMEOUT)

    async with httpx.AsyncClient(follow_redirects=True, headers=headers, timeout=timeout) as client:
        async with client.stream("GET", url) as resp:
            if resp.status_code >= 400:
                return None

            ctype = resp.headers.get("content-type", "").lower()
            if not any(t in ctype for t in ALLOWED_CONTENT_TYPES):
                return None

            chunks: list[bytes] = []
            total = 0

            async for chunk in resp.aiter_bytes():
                total += len(chunk)
                if total > MAX_BYTES:
                    return None
                chunks.append(chunk)

            raw = b"".join(chunks)
            if not raw:
                return None

            # Use encoding detected by httpx, fallback to utf-8
            encoding = resp.encoding or "utf-8"
            try:
                return raw.decode(encoding, errors="ignore")
            except Exception:
                return None


def _extract_main_text(html: str) -> str:
    doc = Document(html)
    clean_html = doc.summary(html_partial=True)

    soup = BeautifulSoup(clean_html, "lxml")
    text = soup.get_text("\n")

    # Collapse excessive blank lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines).strip()


async def extract_url_local(url: str) -> str:
    """Download and extract main text from a URL with safety limits."""

    try:
        html = await _fetch_html(url)
        if not html:
            return ""

        text = await asyncio.to_thread(_extract_main_text, html)
    except Exception:
        return ""

    if not text:
        return ""

    if len(text) > MAX_CHARS:
        return text[:MAX_CHARS].rstrip() + "…"

    return text