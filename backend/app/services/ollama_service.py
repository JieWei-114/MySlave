import httpx
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

async def stream_ollama(prompt: str):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            OLLAMA_URL,
            json={
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": True
            }
        ) as resp:
            async for line in resp.aiter_lines():
                if not line:
                    continue

                data = json.loads(line)

                if "response" in data:
                    yield data['response']

                if data.get("done"):
                    break
