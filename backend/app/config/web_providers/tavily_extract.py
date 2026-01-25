import httpx
from app.config.settings import settings

async def extract_url(url: str) -> str:
    if not settings.TAVILY_API_KEY:
        raise Exception("TAVILY_API_KEY_NOT_SET")

    async with httpx.AsyncClient(timeout=20) as client:
        res = await client.post(
            "https://api.tavily.com/extract",
            json={
                "api_key": settings.TAVILY_API_KEY,
                "urls": [url],
                "include_images": False,
            },
        )

    return res.json()["results"][0]["content"]