from datetime import datetime
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config.ai_models import AVAILABLE_MODELS
from app.core.db import sessions_collection
from app.models.dto import CreateSessionRequest, RenameSessionRequest
from app.services.chat_service import (
    add_message,
    build_prompt_with_memory,
    create_session,
    delete_session,
    get_session,
    list_sessions,
    rename_session,
)
from app.services.ollama_service import stream_ollama
from app.services.memory_service import auto_memory_if_needed


router = APIRouter(prefix='/chat', tags=['chat'])


@router.get('/models')
async def get_available_models():
    return AVAILABLE_MODELS


@router.get('/sessions')
def get_sessions():
    return list_sessions()


@router.post('/session')
def create_chat_session(payload: CreateSessionRequest):
    return create_session(payload.title)


@router.get('/{session_id}')
def get_chat_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')
    return session


@router.get('/{session_id}/stream')
async def stream_message(session_id: str, content: str, model: str):
    try:
        add_message(session_id, 'user', content)
    except ValueError:
        raise HTTPException(status_code=404, detail='Session not found')

    # build prompt with memory
    prompt = build_prompt_with_memory(content, chat_sessionId=session_id)

    async def event_generator():
        assistant_text = ''

        async for token in stream_ollama(prompt, model=model):
            assistant_text += token
            yield f'data: {quote(token)}\n\n'

            await auto_memory_if_needed(
                chat_sessionId=session_id,
                user_text=content,
                assistant_text=assistant_text,
                model=model,
            )

        add_message(session_id, 'assistant', assistant_text)
        yield 'event: done\ndata: end\n\n'

    return StreamingResponse(event_generator(), media_type='text/event-stream')


@router.get('/{session_id}/messages')
def get_messages(session_id: str, limit: int = 20, before: Optional[str] = None):
    session = sessions_collection.find_one({'id': session_id}, {'_id': 0, 'messages': 1})

    if not session:
        return []

    messages = session.get('messages', [])

    messages = sorted(messages, key=lambda m: m['created_at'])

    if before:
        before_dt = datetime.fromisoformat(before.replace('Z', ''))
        messages = [m for m in messages if m['created_at'] < before_dt]

    return messages[-limit:]


@router.patch('/{session_id}/rename')
def rename_chat_session(session_id: str, payload: RenameSessionRequest):
    updated = rename_session(session_id, payload.title)
    if not updated:
        raise HTTPException(status_code=404, detail='Session not found')
    return updated


@router.delete('/{session_id}')
def delete_chat_session(session_id: str):
    ok = delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail='Session not found')
    return {'status': 'deleted'}
