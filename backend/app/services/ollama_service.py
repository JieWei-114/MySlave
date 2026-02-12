"""
Ollama Service
Handles communication with Ollama LLM API
Supports both streaming and non-streaming requests

"""

import json
import logging
from typing import Optional

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)


async def stream_ollama(prompt: str, model: str, system: Optional[str] = None):
    """
    Stream response from Ollama LLM token by token

    """
    logger.info(
        'stream_ollama called with system=%s (type=%s)',
        'present' if system else 'None',
        type(system).__name__,
    )
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
            # Build request payload
            payload = {'model': model, 'prompt': prompt, 'stream': True}
            if system:
                payload['system'] = system
                logger.info('Added system to payload')

            logger.info('Ollama stream payload keys: %s', list(payload.keys()))
            if 'system' in payload:
                logger.info('  Ollama system prompt (len=%s)', len(payload['system']))

            # Stream response
            async with client.stream(
                'POST',
                f'{settings.OLLAMA_URL}/api/generate',
                json=payload,
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

                    # Yield each token
                    if 'response' in data:
                        yield data['response']

                    # Stop when done
                    if data.get('done'):
                        break
    except httpx.HTTPError as exc:
        logger.error('ollama stream request failed: %s', exc)
        return


async def call_ollama_once(prompt: str, model: str, system: Optional[str] = None) -> str:
    """
    Get complete response from Ollama in one call (non-streaming)

    """
    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
            # Build request payload
            payload = {'model': model, 'prompt': prompt, 'stream': False}
            if system:
                payload['system'] = system

            # Make request
            resp = await client.post(
                f'{settings.OLLAMA_URL}/api/generate',
                json=payload,
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
