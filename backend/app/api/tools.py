from fastapi import APIRouter, Query, HTTPException
from app.services.web_search_service import web_search, remaining_quota

router = APIRouter(prefix='/tools', tags=['tools'])

@router.get('/web-search')
async def search(q: str = Query(...)):
    try:
        results = await web_search(q)
        return {
            'results': results,
            'remaining': remaining_quota(),
        }
    except Exception as e:
        raise HTTPException(status_code=429, detail=str(e))
