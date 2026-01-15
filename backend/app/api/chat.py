from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Optional

from app.models.dto import (
    CreateSessionRequest,
    SendMessageRequest,
    RenameSessionRequest
)
from app.services.chat_service import (
    create_session,
    list_sessions,
    get_session,
    delete_session,
    rename_session,
    stream_chat_reply
)
from app.services.ollama_service import stream_ollama
from app.services.chat_service import add_message
from app.core.db import sessions_collection

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/session")
def create_chat_session(payload: CreateSessionRequest):
    return create_session(payload.title)

@router.get("/sessions")
def get_sessions():
    return list_sessions()

@router.get("/{session_id}")
def get_chat_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/{session_id}")
def delete_chat_session(session_id: str):
    ok = delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "deleted"}

@router.patch("/{session_id}/rename")
def rename_chat_session(session_id: str, payload: RenameSessionRequest):
    updated = rename_session(session_id, payload.title)
    if not updated:
        raise HTTPException(status_code=404, detail="Session not found")
    return updated

@router.get("/{session_id}/stream")
async def stream_message(session_id: str, content: str):
    try:
        add_message(session_id, "user", content)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        assistant_text = ""

        async for token in stream_ollama(content):
            assistant_text += token
            yield f"data: {token}\n\n"

        # 👇 streaming 完成后一次性写 DB
        add_message(session_id, "assistant", assistant_text)
        yield "event: done\ndata: end\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

@router.get("/{session_id}/messages")
def get_messages(
    session_id: str,
    limit: int = 20,
    before: Optional[str] = None
):
    session = sessions_collection.find_one(
        {"id": session_id},
        {"_id": 0, "messages": 1}
    )

    if not session:
        return []

    messages = session.get("messages", [])

    # ⏱️ 按时间排序
    messages = sorted(messages, key=lambda m: m["created_at"])

    # 🔁 before 游标
    if before:
        before_dt = datetime.fromisoformat(before)
        messages = [m for m in messages if m["created_at"] < before_dt]

    # ⬅️ 取最后 limit 条
    return messages[-limit:]

