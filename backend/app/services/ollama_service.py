import json
import logging

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)


async def stream_ollama(prompt: str, model: str):
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
            async with client.stream(
                'POST',
                settings.OLLAMA_URL,
                json={'model': model, 'prompt': prompt, 'stream': True},
            ) as resp:
                resp.raise_for_status()

                async for line in resp.aiter_lines():
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning('ollama stream returned non-JSON line: %s', line)
                        continue

                    if 'error' in data:
                        logger.error('ollama stream error: %s', data['error'])
                        break

                    if 'response' in data:
                        yield data['response']

                    if data.get('done'):
                        break
    except httpx.HTTPError as exc:
        logger.error('ollama stream request failed: %s', exc)
        return


async def call_ollama_once(prompt: str, model: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                settings.OLLAMA_URL,
                json={'model': model, 'prompt': prompt, 'stream': False},
            )
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error('ollama call failed: %s', exc)
        return ''

    try:
        return resp.json().get('response', '').strip()
    except (ValueError, AttributeError):
        logger.error('ollama returned invalid JSON body')
        return ''
