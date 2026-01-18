from datetime import datetime
from bson import ObjectId
from app.core.db import memories_collection
from bson.errors import InvalidId

def serialize_memory(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "content": doc["content"],
        "enabled": doc["enabled"],
        "created_at": doc["created_at"],
        "chat_sessionId": doc["chat_sessionId"],
    }

def list_enabled_memories(chat_sessionId: str):
    cursor = memories_collection.find(
        {"chat_sessionId": chat_sessionId, "enabled": True},
    ).sort("created_at", 1)

    return [serialize_memory(doc) for doc in cursor]

def list_all_memories(chat_sessionId: str):
    cursor = memories_collection.find(
        {"chat_sessionId": chat_sessionId}
    ).sort("created_at", 1)
    return [serialize_memory(doc) for doc in cursor]

def add_memory(content: str, chat_sessionId: str, source: str = "manual"):
    memory = {
        "chat_sessionId": chat_sessionId,
        "content": content,
        "source": source,
        "enabled": True,
        "created_at": datetime.utcnow()
    }
    result = memories_collection.insert_one(memory)
    memory["_id"] = result.inserted_id
    return serialize_memory(memory)

def set_memory_enabled(memory_id: str, enabled: bool):
    memories_collection.update_one(
        {"_id": ObjectId(memory_id)},
        {"$set": {"enabled": enabled}}
    )

def delete_memory(memory_id: str):
    try:
        oid = ObjectId(memory_id)
    except InvalidId:
        raise ValueError("Invalid memory id")

    memories_collection.delete_one({"_id": oid})