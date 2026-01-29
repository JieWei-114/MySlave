import logging
import re
from typing import Optional

from app.config.web_providers.ddg import DuckDuckGoProvider
from app.config.web_providers.local_extract import extract_url_local
from app.config.web_providers.searxng import SearXNGProvider
from app.config.web_providers.serper import SerperProvider, remaining_serper_quota
from app.config.web_providers.tavily import TavilyProvider, remaining_tavily_quota
from app.config.web_providers.tavily_extract import extract_url
from app.core.db import rules_collection, sessions_collection

logger = logging.getLogger(__name__)

serper = SerperProvider()
searxng = SearXNGProvider()
ddg = DuckDuckGoProvider()
tavily = TavilyProvider()


def get_enabled_rules(session_id: Optional[str] = None) -> dict:
    try:
        if session_id:
            session = sessions_collection.find_one({'id': session_id}, {'_id': 0, 'rules': 1})
            if session and session.get('rules'):
                return session['rules']

        rules = rules_collection.find_one({}, {'_id': 0})
        if not rules:
            #  Returns default (all enabled) if no rules are stored.
            return {
                'searxng': True,
                'duckduckgo': True,
                'tavily': True,
                'serper': True,
                'tavilyExtract': True,
                'localExtract': True,
            }
        return rules
    except Exception as e:
        logger.warning(f'Failed to fetch rules, using defaults: {e}')
        return {
            'searxng': True,
            'duckduckgo': True,
            'tavily': True,
            'serper': True,
            'tavilyExtract': True,
            'localExtract': True,
        }


# Command keywords
EXPLICIT_COMMANDS = {
    'super search': serper,
    'tavily search': tavily,
}

AUTO_ROUTE_KEYWORDS = {
    'serper': ['today', 'latest', 'current', 'news'],
    'tavily': ['research', 'deep dive', 'detailed'],
}

URL_PATTERN = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
    re.IGNORECASE,
)


def is_url(text: str) -> bool:
    # Validate URL format
    match = URL_PATTERN.search(text.strip())
    return match is not None


def extract_url_from_text(text: str) -> Optional[str]:
    # Extract first URL found in text
    match = URL_PATTERN.search(text.strip())
    return match.group(0) if match else None


async def maybe_web_search(
    query: str, limit: int = 5, session_id: Optional[str] = None
) -> list[dict]:
    """
    web search routing with rule-based filtering.

    Priority:
    1. Check enabled rules - skip disabled providers
    2. Explicit commands ("super search", "tavily search")
    3. "advance search" → all enabled providers
    4. Auto-routing based on keywords
    5. Default: SearXNG → DuckDuckGo fallback (if enabled)
    """

    if not query or not query.strip():
        logger.warning('Empty search query')
        return []

    # Get current rule configuration
    rules = get_enabled_rules(session_id=session_id)
    logger.info(f'Current rules: {rules}')
    logger.info(
        f'Current quotas - Serper: {remaining_serper_quota()}, Tavily: {remaining_tavily_quota()}'
    )

    query = query.strip()
    q_lower = query.lower()

    # Explicit commands
    for cmd, provider in EXPLICIT_COMMANDS.items():
        if cmd in q_lower:
            # Check if provider is enabled
            provider_key = provider.name.lower()
            if provider_key in rules and not rules[provider_key]:
                logger.warning(f'{provider.name} is disabled by rules, skipping')
                return []

            logger.info(f"Explicit command '{cmd}' matched, using {provider.name}")
            try:
                return await provider.search(query, limit)
            except Exception as e:
                logger.error(f'{provider.name} search failed: {e}')
                return []

    # Advance search: all enabled providers
    if 'advance search' in q_lower:
        logger.info('Advance search triggered, querying enabled providers')
        results = []
        seen_urls = set()

        # Only query enabled providers
        enabled_providers = []
        if rules.get('tavily', True):
            enabled_providers.append(tavily)
        if rules.get('serper', True):
            enabled_providers.append(serper)
        if rules.get('searxng', True):
            enabled_providers.append(searxng)
        if rules.get('duckduckgo', True):
            enabled_providers.append(ddg)

        for provider in enabled_providers:
            try:
                provider_results = await provider.search(query, limit)
                for r in provider_results:
                    url = r.get('link', '')
                    if url not in seen_urls:
                        results.append(r)
                        seen_urls.add(url)
            except Exception as e:
                logger.warning(f'{provider.name} failed in advance search: {e}')
                continue

        return results[: limit * 2]

    # Auto routing
    for provider_name, keywords in AUTO_ROUTE_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            # Check if the auto-routed provider is enabled
            if not rules.get(provider_name, True):
                logger.info(f'Auto-routing to {provider_name} skipped (disabled by rules)')
                break

            provider = serper if provider_name == 'serper' else tavily
            logger.info(f'Auto-routing to {provider.name} (keyword match)')
            try:
                return await provider.search(query, limit)
            except Exception as e:
                logger.warning(f'{provider.name} auto-route failed: {e}')
                break

    # Default (if enabled)
    logger.info('Using default routing: SearXNG → DuckDuckGo')

    # Try SearXNG if enabled
    if rules.get('searxng', True):
        try:
            results = await searxng.search(query, limit)
            if results:
                logger.info(f'SearXNG returned {len(results)} results')
                return results
        except Exception as e:
            logger.warning(f'SearXNG failed: {e}')
    else:
        logger.info('SearXNG disabled by rules')

    # Fallback to DuckDuckGo if enabled
    if rules.get('duckduckgo', True):
        try:
            results = await ddg.search(query, limit)
            logger.info(f'DuckDuckGo fallback returned {len(results)} results')
            return results
        except Exception as e:
            logger.error(f'DuckDuckGo failed: {e}')
    else:
        logger.info('DuckDuckGo disabled by rules')

    # Fallback to tavily if enabled
    if rules.get('tavily', True):
        try:
            results = await tavily.search(query, limit)
            logger.info(f'tavily fallback returned {len(results)} results')
            return results
        except Exception as e:
            logger.error(f'tavily failed: {e}')
    else:
        logger.info('tavily disabled by rules')

    # Fallback to serper if enabled
    if rules.get('serper', True):
        try:
            results = await serper.search(query, limit)
            logger.info(f'serper fallback returned {len(results)} results')
            return results
        except Exception as e:
            logger.error(f'serper failed: {e}')
    else:
        logger.info('serper disabled by rules')

    logger.error('All search providers failed or disabled')
    return []


async def maybe_extract(user_text: str, session_id: Optional[str] = None) -> str:
    """
    URL extraction routing with rule-based filtering.

    Priority:
    1. Check enabled rules - skip disabled extraction methods
    2. Explicit commands ("tavily extract", "local extract")
    3. Default: Tavily → Local fallback (if enabled)
    4. Returns empty string on all failures
    """

    if not user_text or not user_text.strip():
        return ''

    # Get current rule configuration
    rules = get_enabled_rules(session_id=session_id)
    logger.info(f'Current rules: {rules}')
    logger.info(f'Current quotas - Tavily: {remaining_tavily_quota()}')

    # Clean the text: replace newlines with spaces and remove extra padding
    cleaned_text = ' '.join(user_text.strip().split())
    text_lower = cleaned_text.lower()

    # Detect URL in text
    url = extract_url_from_text(cleaned_text)
    if not url:
        logger.debug('No URL detected in extraction request')
        return ''

    # Explicit commands
    if 'tavily extract' in text_lower:
        if not rules.get('tavilyExtract', True):
            logger.warning('Tavily extract disabled by rules')
            return ''

        logger.info(f'Tavily extract requested for {url}')
        try:
            return await extract_url(url)
        except Exception as e:
            logger.error(f'Tavily extract failed: {e}')
            return ''

    if 'local extract' in text_lower:
        if not rules.get('localExtract', True):
            logger.warning('Local extract disabled by rules')
            return ''

        logger.info(f'Local extract requested for {url}')
        try:
            return await extract_url_local(url)
        except Exception as e:
            logger.error(f'Local extract failed: {e}')
            return ''

    # Default: Tavily → Local fallback (if enabled)
    logger.info(f'Default extraction for {url}: Tavily → Local')

    # Try Tavily if enabled
    if rules.get('tavilyExtract', True):
        try:
            result = await extract_url(url)
            if result:
                logger.info('Tavily extract succeeded')
                return result
        except Exception as e:
            logger.warning(f'Tavily extract failed, falling back to local: {e}')
    else:
        logger.info('Tavily extract disabled by rules, trying local')

    # Fallback to Local if enabled
    if rules.get('localExtract', True):
        try:
            result = await extract_url_local(url)
            logger.info('Local extract fallback succeeded')
            return result
        except Exception as e:
            logger.error(f'Local extract failed: {e}')
    else:
        logger.info('Local extract disabled by rules')

    logger.error('All extraction methods failed or disabled')
    return ''
