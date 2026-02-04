import json
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.config.ai_models import AVAILABLE_MODELS
from app.core.db import sessions_collection
from app.config.settings import settings
from app.models.dto import (
    AttachFileRequest,
    CreateSessionRequest,
    RenameSessionRequest,
    ReorderSessionsRequest,
)
from app.services.chat_service import (
    create_session,
    delete_session,
    get_session,
    list_sessions,
    rename_session,
    stream_chat_reply,
)
from app.services.file_extraction_service import extract_text_from_file, truncate_content

router = APIRouter(prefix='/chat', tags=['chat'])
logger = logging.getLogger(__name__)


def detect_file_type(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith('.pdf'):
        return 'PDF'
    if lower.endswith(('.docx', '.doc')):
        return 'Word'
    if lower.endswith(('.txt', '.md')):
        return 'Text'
    if lower.endswith(('.json', '.yaml', '.yml')):
        return 'Config'
    if lower.endswith(('.py', '.js', '.ts', '.java', '.cpp')):
        return 'Code'
    return 'unknown'


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
    async def event_generator():
        async for chunk in stream_chat_reply(session_id, content, model):

            if isinstance(chunk, bytes):
                chunk = chunk.decode("utf-8")

            chunk = chunk.strip()
            if not chunk:
                continue

            try:
                payload = json.loads(chunk)

                if payload.get('type') == 'done':
                    yield (
                        "event: done\n"
                        f"data: {json.dumps(payload)}\n\n"
                    )

                elif payload.get('type') == 'token':
                    yield (
                        "event: token\n"
                        f"data: {json.dumps(payload['data'])}\n\n"
                    )

                elif payload.get('type') == 'error':
                    yield (
                        "event: error\n"
                        f"data: {json.dumps(payload)}\n\n"
                    )

            except json.JSONDecodeError:
                # normal token
                yield f"data: {quote(chunk)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
    )


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


@router.post('/reorder')
def reorder_sessions(payload: ReorderSessionsRequest):
    try:
        sessions_collection.update_one(
            {'id': '__order__'},
            {
                '$set': {
                    'id': '__order__',
                    'sessionIds': payload.sessionIds,
                    'updated_at': datetime.utcnow(),
                }
            },
            upsert=True,
        )
        return {'status': 'reordered'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to reorder sessions: {str(e)}')


@router.post('/upload')
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and extract content from files (PDF, Word, text files).
    Returns extracted text content.
    """
    try:
        # Read file content
        file_content = await file.read()

        # Check file size
        max_size = settings.FILE_UPLOAD_MAX_SIZE_MB * 1024 * 1024
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f'File too large. Max {settings.FILE_UPLOAD_MAX_SIZE_MB}MB.',
            )

        # Extract text content
        try:
            extracted_text = extract_text_from_file(file_content, file.filename)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Truncate if too long (50k chars ~ 12.5k tokens)
        truncated_text = truncate_content(extracted_text, max_chars=50000)

        return {
            'content': truncated_text,
            'filename': file.filename,
            'original_size': len(file_content),
            'extracted_length': len(truncated_text),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to process file: {str(e)}')


@router.post('/{session_id}/attachment')
def attach_file(session_id: str, payload: AttachFileRequest):
    """
    Attach extracted file content to a session (used on next prompt only).
    """
    session = sessions_collection.find_one({'id': session_id}, {'_id': 0, 'id': 1})
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')

    filename = payload.filename.strip()
    content = payload.content.strip() if payload.content else ''

    if not filename or not content:
        raise HTTPException(status_code=400, detail='filename and content are required')

    truncated = truncate_content(content)

    sessions_collection.update_one(
        {'id': session_id},
        {
            '$set': {
                'pending_attachment': {
                    'filename': filename,
                    'content': truncated,
                    'length': len(truncated),
                    'type': detect_file_type(filename),
                    'created_at': datetime.utcnow(),
                }
            }
        },
    )

    return {
        'status': 'attached',
        'filename': filename,
        'length': len(truncated),
    }
