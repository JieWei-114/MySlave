from fastapi import APIRouter, HTTPException, Query

from app.config.web_providers.serper import remaining_serper_quota
from app.config.web_providers.tavily import remaining_tavily_quota
from app.services.web_search_service import maybe_web_search

router = APIRouter(prefix='/web', tags=['web'])


@router.get('/web-search')
async def web_search(q: str = Query(...), limit: int = None, session_id: str | None = None):
    try:
        results = await maybe_web_search(q, limit, session_id=session_id)
        return {
            'results': results,
            'quotas': {
                'serper_remaining': remaining_serper_quota(),
                'tavily_remaining': remaining_tavily_quota(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get('/quotas')
def get_quotas():
    return {
        'serper_remaining': remaining_serper_quota(),
        'tavily_remaining': remaining_tavily_quota(),
    }
