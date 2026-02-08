"""
Web Search Service

Multi-provider web search and URL extraction service.
Supports multiple search providers with automatic fallback and smart routing.

Supported Providers:
- SearXNG: Self-hosted metasearch (privacy-focused)
- DuckDuckGo: Simple web search (free)
- Tavily: Research-focused search (paid API)
- Serper: Google search proxy (paid API)

URL Extraction:
- TavilyExtract: AI-powered content extraction (paid API)
- LocalExtract: Simple HTML parsing (free)

"""
import logging
import re
from typing import Optional

from app.config.settings import settings
from app.config.web_providers.ddg import DuckDuckGoProvider
from app.config.web_providers.local_extract import extract_url_local
from app.config.web_providers.searxng import SearXNGProvider
from app.config.web_providers.serper import SerperProvider, remaining_serper_quota
from app.config.web_providers.tavily import TavilyProvider, remaining_tavily_quota
from app.config.web_providers.tavily_extract import extract_url
from app.core.db import rules_collection, sessions_collection
from app.models.dto import RulesConfig

logger = logging.getLogger(__name__)

# Providers
serper = SerperProvider()
searxng = SearXNGProvider()
ddg = DuckDuckGoProvider()
tavily = TavilyProvider()

# Centralized limit settings
RESULTS_PER_PROVIDER = settings.WEB_SEARCH_RESULTS_PER_PROVIDER
ADVANCE_SEARCH_TOTAL = settings.WEB_SEARCH_ADVANCE_TOTAL

# Auto-routing keywords for Tavily (research-focused queries)
# If query contains these words and Tavily is enabled, route to Tavily
TAVILY_KEYWORDS = settings.WEB_TAVILY_KEYWORDS

URL_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    re.IGNORECASE,
)

# ============================================================
# Rules
# ============================================================

DEFAULT_RULES = RulesConfig().model_dump()


def get_enabled_rules(session_id: Optional[str] = None) -> dict:
    """
    Get enabled search providers and search settings for a session.

    """
    try:
        if session_id:
            session = sessions_collection.find_one(
                {'id': session_id},
                {'_id': 0, 'rules': 1},
            )
            if session and session.get('rules'):
                return {**DEFAULT_RULES, **session['rules']}

        rules = rules_collection.find_one({}, {'_id': 0})
        if rules:
            return {**DEFAULT_RULES, **rules}

        return DEFAULT_RULES.copy()

    except Exception as e:
        logger.warning(f'Failed to fetch rules, using defaults: {e}')
        return DEFAULT_RULES.copy()


# ============================================================
# Web Search
# ============================================================


async def maybe_web_search(
    query: str,
    limit: Optional[int] = None,
    session_id: Optional[str] = None,
) -> list[dict]:
    """
    Perform multi-provider web search with intelligent routing.

    """
    if not query or not query.strip():
        logger.warning('Empty search query')
        return []

    if limit is None:
        limit = RESULTS_PER_PROVIDER

    rules = get_enabled_rules(session_id)
    logger.info(f'Current rules: {rules}')
    logger.info(
        f'Current quotas - Serper: {remaining_serper_quota()}, Tavily: {remaining_tavily_quota()}'
    )

    query = query.strip()
    q_lower = query.lower()

    # ---------------------------------------------------------------
    # Advance Search
    # ---------------------------------------------------------------
    if rules['advanceSearch']:
        logger.info('Advance search mode enabled')

        providers = []
        if rules['tavily']:
            providers.append(tavily)
        if rules['serper']:
            providers.append(serper)
        if rules['searxng']:
            providers.append(searxng)
        if rules['duckduckgo']:
            providers.append(ddg)

        if not providers:
            logger.warning('Advance search: all providers disabled')
            return []

        per_provider = max(1, ADVANCE_SEARCH_TOTAL // len(providers))
        results: list[dict] = []
        seen_urls: set[str] = set()

        for provider in providers:
            try:
                provider_results = await provider.search(query, per_provider)
                for r in provider_results:
                    url = r.get('link')
                    if not url or url in seen_urls:
                        continue

                    results.append(r)
                    seen_urls.add(url)

                    if len(results) >= ADVANCE_SEARCH_TOTAL:
                        break
            except Exception as e:
                logger.warning(f'{provider.name} failed in advance search: {e}')

            if len(results) >= ADVANCE_SEARCH_TOTAL:
                break

        logger.info(f'Advance search returning {len(results)} results')
        return results[:ADVANCE_SEARCH_TOTAL]

    # ---------------------------------------------------------------
    # Auto-route to Tavily (research queries)
    # ---------------------------------------------------------------
    if rules['tavily'] and any(kw in q_lower for kw in TAVILY_KEYWORDS):
        logger.info('Auto-routing to Tavily (research query)')
        try:
            return await tavily.search(query, limit)
        except Exception as e:
            logger.warning(f'Tavily auto-route failed: {e}')

    # ---------------------------------------------------------------
    # Default provider chain
    # ---------------------------------------------------------------
    logger.info('Using default search routing')

    if rules['searxng']:
        try:
            results = await searxng.search(query, limit)
            if results:
                return results
        except Exception as e:
            logger.warning(f'SearXNG failed: {e}')

    if rules['duckduckgo']:
        try:
            return await ddg.search(query, limit)
        except Exception as e:
            logger.warning(f'DuckDuckGo failed: {e}')

    if rules['tavily']:
        try:
            return await tavily.search(query, limit)
        except Exception as e:
            logger.warning(f'Tavily failed: {e}')

    if rules['serper']:
        try:
            return await serper.search(query, limit)
        except Exception as e:
            logger.warning(f'Serper failed: {e}')

    logger.error('All search providers failed or disabled')
    return []


# ============================================================
# URL Extraction
# ============================================================


def extract_url_from_text(text: str) -> Optional[str]:
    # Extract first URL found in text
    match = URL_PATTERN.search(text.strip())
    return match.group(0) if match else None


async def maybe_extract(
    user_text: str,
    session_id: Optional[str] = None,
) -> str:
    if not user_text or not user_text.strip():
        return ''

    rules = get_enabled_rules(session_id)

    cleaned_text = ' '.join(user_text.strip().split())
    url = extract_url_from_text(cleaned_text)

    if not url:
        logger.debug('No URL detected')
        return ''

    # ---------------------------------------------------------------
    # Advance Extract
    # ---------------------------------------------------------------
    if rules['advanceExtract']:
        logger.info(f'Advance extract for {url}')
        results: list[str] = []

        if rules['localExtract']:
            try:
                content = await extract_url_local(url)
                if content:
                    results.append(f'[Local]\n{content}')
            except Exception as e:
                logger.warning(f'Local extract failed: {e}')

        if rules['tavilyExtract']:
            try:
                content = await extract_url(url)
                if content:
                    results.append(f'[Tavily]\n{content}')
            except Exception as e:
                logger.warning(f'Tavily extract failed: {e}')

        return '\n---\n'.join(results) if results else ''

    # ---------------------------------------------------------------
    # Default: Local → Tavily
    # ---------------------------------------------------------------
    logger.info(f'Default extract for {url}')

    if rules['localExtract']:
        try:
            content = await extract_url_local(url)
            if content:
                return content
        except Exception as e:
            logger.warning(f'Local extract failed: {e}')

    if rules['tavilyExtract']:
        try:
            return await extract_url(url)
        except Exception as e:
            logger.warning(f'Tavily extract failed: {e}')

    logger.error('All extraction methods failed or disabled')
    return ''
