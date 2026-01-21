import json

import httpx

from app.config.settings import settings


async def stream_ollama(prompt: str, model: str):
    async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
        async with client.stream(
            'POST', settings.OLLAMA_URL, json={'model': model, 'prompt': prompt, 'stream': True}
        ) as resp:
            async for line in resp.aiter_lines():
                if not line:
                    continue

                data = json.loads(line)

                if 'response' in data:
                    yield data['response']

                if data.get('done'):
                    break
