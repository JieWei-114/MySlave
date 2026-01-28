import logging
import re
from typing import Optional

from app.config.web_providers.serper import SerperProvider
from app.config.web_providers.searxng import SearXNGProvider
from app.config.web_providers.ddg import DuckDuckGoProvider
from app.config.web_providers.tavily import TavilyProvider
from app.config.web_providers.local_extract import extract_url_local
from app.config.web_providers.tavily_extract import extract_url

logger = logging.getLogger(__name__)

serper = SerperProvider()
searxng = SearXNGProvider()
ddg = DuckDuckGoProvider()
tavily = TavilyProvider()

# Command keywords
EXPLICIT_COMMANDS = {
    "super search": serper,
    "tavily search": tavily,
}

AUTO_ROUTE_KEYWORDS = {
    "serper": ["who is", "ceo", "today", "latest", "current", "news"],
    "tavily": ["research", "deep dive", "detailed"],
}

URL_PATTERN = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)


def is_url(text: str) -> bool:
    """Validate URL format."""
    return bool(URL_PATTERN.match(text.strip()))


async def maybe_web_search(query: str, limit: int = 5) -> list[dict]:
    """
    Smart web search routing.
    
    Priority:
    1. Explicit commands ("super search", "tavily search")
    2. "advance search" → all providers
    3. Auto-routing based on keywords
    4. Default: SearXNG → DuckDuckGo fallback
    """
    
    if not query or not query.strip():
        logger.warning("Empty search query")
        return []
    
    query = query.strip()
    q_lower = query.lower()

    # ===== Explicit commands =====
    for cmd, provider in EXPLICIT_COMMANDS.items():
        if cmd in q_lower:
            logger.info(f"Explicit command '{cmd}' matched, using {provider.name}")
            try:
                return await provider.search(query, limit)
            except Exception as e:
                logger.error(f"{provider.name} search failed: {e}")
                return []

    # ===== Advance search: all providers =====
    if "advance search" in q_lower:
        logger.info("Advance search triggered, querying all providers")
        results = []
        seen_urls = set()

        for provider in [tavily, serper, searxng, ddg]:
            try:
                provider_results = await provider.search(query, limit)
                for r in provider_results:
                    url = r.get("link", "")
                    if url not in seen_urls:
                        results.append(r)
                        seen_urls.add(url)
            except Exception as e:
                logger.warning(f"{provider.name} failed in advance search: {e}")
                continue

        return results[:limit * 2]

    # ===== Auto routing =====
    for provider_name, keywords in AUTO_ROUTE_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            provider = serper if provider_name == "serper" else tavily
            logger.info(f"Auto-routing to {provider.name} (keyword match)")
            try:
                return await provider.search(query, limit)
            except Exception as e:
                logger.warning(f"{provider.name} auto-route failed: {e}")
                break

    # ===== Default: SearXNG → DuckDuckGo =====
    logger.info("Using default routing: SearXNG → DuckDuckGo")
    try:
        results = await searxng.search(query, limit)
        if results:
            logger.info(f"SearXNG returned {len(results)} results")
            return results
    except Exception as e:
        logger.warning(f"SearXNG failed: {e}")

    try:
        results = await ddg.search(query, limit)
        logger.info(f"DuckDuckGo fallback returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"All search providers failed: {e}")
        return []


async def maybe_extract(user_text: str) -> str:
    """
    Smart URL extraction routing.
    
    Priority:
    1. Explicit commands ("tavily extract", "local extract", "extract both")
    2. Default: Tavily → Local fallback
    3. Returns empty string on all failures
    """
    
    if not user_text or not user_text.strip():
        return ""

    user_text = user_text.strip()
    
    # Detect URL in text
    url = None
    for word in user_text.split():
        if is_url(word):
            url = word
            break
    
    if not url:
        logger.debug("No URL detected in extraction request")
        return ""

    text_lower = user_text.lower()

    # ===== Explicit commands =====
    if "tavily extract" in text_lower:
        logger.info(f"Tavily extract requested for {url}")
        try:
            return await extract_url(url)
        except Exception as e:
            logger.error(f"Tavily extract failed: {e}")
            return ""

    if "local extract" in text_lower:
        logger.info(f"Local extract requested for {url}")
        try:
            return await extract_url_local(url)
        except Exception as e:
            logger.error(f"Local extract failed: {e}")
            return ""

    if "extract both" in text_lower:
        logger.info(f"Extract both requested for {url}")
        cloud = ""
        local = ""
        
        try:
            cloud = await extract_url(url)
        except Exception as e:
            logger.warning(f"Tavily extract failed: {e}")

        try:
            local = await extract_url_local(url)
        except Exception as e:
            logger.warning(f"Local extract failed: {e}")

        result = ""
        if cloud:
            result += f"[TAVILY]\n{cloud}"
        if local:
            result += f"\n\n[LOCAL]\n{local}" if result else f"[LOCAL]\n{local}"
        
        return result

    # ===== Default: Tavily → Local fallback =====
    logger.info(f"Default extraction for {url}: Tavily → Local")
    try:
        result = await extract_url(url)
        if result:
            logger.info("Tavily extract succeeded")
            return result
    except Exception as e:
        logger.warning(f"Tavily extract failed, falling back to local: {e}")

    try:
        result = await extract_url_local(url)
        logger.info("Local extract fallback succeeded")
        return result
    except Exception as e:
        logger.error(f"Both extraction methods failed: {e}")
        return ""