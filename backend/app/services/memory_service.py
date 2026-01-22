from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId

from app.core.db import memories_collection
from app.services.embedding_service import embed, cosine_similarity
from app.services.ollama_service import call_ollama_once

def serialize_memory(doc: dict) -> dict:
    return {
        'id': str(doc['_id']),
        'content': doc['content'],
        'enabled': doc['enabled'],
        'created_at': doc['created_at'],
        'chat_sessionId': doc['chat_sessionId'],
    }


def add_memory(content: str, chat_sessionId: str, source: str = 'manual'):
    embedding = embed(content)
    memory = {
        'chat_sessionId': chat_sessionId,
        'content': content,
        'embedding': embedding,
        'source': source,
        'enabled': True,
        'created_at': datetime.utcnow(),
    }
    result = memories_collection.insert_one(memory)
    memory['_id'] = result.inserted_id
    return serialize_memory(memory)


def list_all_memories(chat_sessionId: str):
    cursor = memories_collection.find({'chat_sessionId': chat_sessionId}).sort('created_at', 1)
    return [serialize_memory(doc) for doc in cursor]


def set_memory_enabled(memory_id: str, enabled: bool):
    memories_collection.update_one({'_id': ObjectId(memory_id)}, {'$set': {'enabled': enabled}})


def list_enabled_memories(chat_sessionId: str):
    cursor = memories_collection.find(
        {'chat_sessionId': chat_sessionId, 'enabled': True},
    ).sort('created_at', 1)

    return [serialize_memory(doc) for doc in cursor]


def delete_memory(memory_id: str):
    try:
        oid = ObjectId(memory_id)
    except InvalidId:
        raise ValueError('Invalid memory id')

    memories_collection.delete_one({'_id': oid})


def delete_memories_for_session(chat_sessionId: str) -> int:
    """Delete all memories linked to a chat session. Returns deleted count."""
    result = memories_collection.delete_many({'chat_sessionId': chat_sessionId})
    return result.deleted_count

def search_memories(chat_sessionId: str, query: str, limit: int = 5):
    query_vec = embed(query)

    cursor = memories_collection.find({
        'chat_sessionId': chat_sessionId,
        'enabled': True,
        'embedding': {'$exists': True},
    })

    scored = []
    for doc in cursor:
        score = cosine_similarity(query_vec, doc['embedding'])
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    return [serialize_memory(d[1]) for d in scored[:limit]]

async def compress_memories(chat_sessionId: str, model: str):
    memories = list_enabled_memories(chat_sessionId)

    if len(memories) < 2:
        return None

    text = '\n'.join(f"- {m['content']}" for m in memories)

    prompt = f"""
Summarize the following memories into a concise, structured long-term memory.
Do not lose important facts.
Do not add explanation.

Memories:
{text}
"""

    summary = await call_ollama_once(prompt, model)

    return add_memory(
        content=summary,
        chat_sessionId=chat_sessionId,
        source='compress',
    )

MIN_LEN = 10

def should_remember(text: str) -> bool:
    return len(text) >= MIN_LEN

async def summarize(text: str, model: str) -> str:
    prompt = f"""
Summarize the following content into a single concise fact.
Do NOT add explanation.

Content:
{text}
"""
    return await call_ollama_once(prompt, model)

async def auto_memory_if_needed(
    chat_sessionId: str,
    user_text: str,
    assistant_text: str,
    model: str,
):
    combined = f"User: {user_text}\nAssistant: {assistant_text}"

    if not should_remember(combined):
        return None

    summary = await summarize(combined, model)

    return add_memory(
        content=summary,
        chat_sessionId=chat_sessionId,
        source='auto',
    )
