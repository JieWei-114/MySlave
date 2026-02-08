"""
Web Search API

"""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.config.web_providers.serper import remaining_serper_quota
from app.config.web_providers.tavily import remaining_tavily_quota
from app.services.web_search_service import maybe_web_search

from app.config.constants import (
    HTTP_INTERNAL_ERROR, HTTP_TOO_MANY_REQUEST
)

router = APIRouter(prefix='/web', tags=['web'])
logger = logging.getLogger(__name__)


@router.get('/web-search')
async def web_search(q: str = Query(...), limit: int = None, session_id: str | None = None):
    """
    Perform multi-provider web search with smart provider routing.
    
    """
    try:
        logger.info('Web search requested (query_len=%s, limit=%s, session_id=%s)', len(q), limit, session_id)
        results = await maybe_web_search(q, limit, session_id=session_id)
        return {
            'results': results,
            'quotas': {
                'serper_remaining': remaining_serper_quota(),
                'tavily_remaining': remaining_tavily_quota(),
            },
        }
    except Exception as e:
        logger.error('Web search failed: %s', e, exc_info=True)
        raise HTTPException(status_code=HTTP_TOO_MANY_REQUEST, detail=str(e))


@router.get('/quotas')
def get_quotas():
    """
    Get remaining API quota for paid web search providers.

    """
    try:
      return {
        'serper_remaining': remaining_serper_quota(),
        'tavily_remaining': remaining_tavily_quota(),
      }
    except Exception as e:
      logger.error('Failed to fetch quotas: %s', e, exc_info=True)
      raise HTTPException(status_code=HTTP_INTERNAL_ERROR, detail='Failed to fetch quotas')