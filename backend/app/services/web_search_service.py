from app.config.web_providers.serper import SerperProvider
from app.config.web_providers.searxng import SearXNGProvider
from app.config.web_providers.ddg import DuckDuckGoProvider
from app.config.web_providers.tavily import TavilyProvider
from app.config.web_providers.local_extract import extract_url_local
from app.config.web_providers.tavily_extract import extract_url

serper = SerperProvider()
searxng = SearXNGProvider()
ddg = DuckDuckGoProvider()
tavily = TavilyProvider()


async def maybe_web_search(query: str, limit: int = 5) -> list[dict]:
    q = query.lower()

    # ===== Explicit commands =====
    if "super search" in q:
        return await serper.search(query, limit)

    if "tavily search" in q:
        return await tavily.search(query, limit)

    if "advance search" in q:
        results = []

        for provider in (searxng, ddg, tavily, serper):
            try:
                results += await provider.search(query, limit)
            except Exception:
                pass

        return results[: limit * 2]

    # ===== Auto routing =====
    if any(k in q for k in ['who is', 'ceo', 'today', 'latest']):
        try:
            return await serper.search(query, limit)
        except Exception:
            pass

    # default
    try:
        return await searxng.search(query, limit)
    except Exception:
        return await ddg.search(query, limit)
    
def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")

async def maybe_extract(user_text: str) -> str | None:
    text = user_text.lower()

    if not is_url(user_text):
        return None

    if "tavily extract" in text:
        return await extract_url(user_text)

    if "local extract" in text:
        return await extract_url_local(user_text)

    if "extract both" in text:
        try:
            cloud = await extract_url(user_text)
        except Exception:
            cloud = ""

        local = await extract_url_local(user_text)
        return f"[TAVILY]\n{cloud}\n\n[LOCAL]\n{local}"

    # default: cloud → local fallback
    try:
        return await extract_url(user_text)
    except Exception:
        return await extract_url_local(user_text)
