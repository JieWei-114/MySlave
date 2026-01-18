from fastapi import APIRouter, Query, HTTPException
from app.services.memory_service import (
    list_all_memories,
    add_memory,
    set_memory_enabled,
    delete_memory
)
from app.models.dto import CreateMemoryRequest

router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/")
def get_memories(
    chat_sessionId: str = Query(...)
):
    return list_all_memories(chat_sessionId)

@router.post("/")
def create_memory(payload: CreateMemoryRequest):
    return add_memory(payload.content,payload.chat_sessionId)

@router.patch("/{memory_id}/enable")
def enable_memory(memory_id: str):
    set_memory_enabled(memory_id, True)
    return {"status": "enabled"}


@router.patch("/{memory_id}/disable")
def disable_memory(memory_id: str):
    set_memory_enabled(memory_id, False)
    return {"status": "disabled"}


@router.delete("/{memory_id}")
def remove_memory(memory_id: str):
    try:
        delete_memory(memory_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory id")