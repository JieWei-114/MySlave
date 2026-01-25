from fastapi import APIRouter, Query, HTTPException

from app.services.web_search_service import maybe_web_search
from app.config.web_providers.serper import remaining_serper_quota
from app.config.web_providers.tavily import remaining_tavily_quota

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("/web-search")
async def web_search(q: str = Query(...), limit: int = 5):
    try:
        results = await maybe_web_search(q, limit)
        return {
            "results": results,
            "quotas": {
                "serper_remaining": remaining_serper_quota(),
                "tavily_remaining": remaining_tavily_quota(),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=429, detail=str(e))


@router.get("/quotas")
def get_quotas():
    return {
        "serper_remaining": remaining_serper_quota(),
        "tavily_remaining": remaining_tavily_quota(),
    }
