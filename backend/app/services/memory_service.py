from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId

from app.core.db import memories_collection
from app.services.embedding_service import cosine_similarity, embed
from app.services.ollama_service import call_ollama_once

MAX_CONTENT_LENGTH = 2000


def serialize_memory(doc: dict) -> dict:
    return {
        'id': str(doc['_id']),
        'content': doc['content'],
        'enabled': doc['enabled'],
        'created_at': doc['created_at'],
        'chat_sessionId': doc['chat_sessionId'],
        'source': doc.get('source', 'manual'),
    }


# def add_memory(content: str, chat_sessionId: str, source: str = 'manual'):
#     embedding = embed(content)
#     memory = {
#         'chat_sessionId': chat_sessionId,
#         'content': content,
#         'embedding': embedding,
#         'source': source,
#         'enabled': True,
#         'created_at': datetime.utcnow(),
#     }
#     result = memories_collection.insert_one(memory)
#     memory['_id'] = result.inserted_id
#     return serialize_memory(memory)


def add_memory(content: str, chat_sessionId: str, source: str = 'manual'):
    if not content or not content.strip():
        raise ValueError('Content cannot be empty')

    if len(content) > MAX_CONTENT_LENGTH:
        content = content[:MAX_CONTENT_LENGTH]

    try:
        embedding = embed([content])[0]
    except Exception as e:
        raise ValueError(f'Failed to generate embedding: {e}')

    memory = {
        'chat_sessionId': chat_sessionId,
        'content': content.strip(),
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
    try:
        oid = ObjectId(memory_id)
    except InvalidId:
        raise ValueError('Invalid memory id')

    memories_collection.update_one({'_id': oid}, {'$set': {'enabled': enabled}})


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


# def search_memories(chat_sessionId: str, query: str, limit: int = 5):
#     query_vec = embed(query)

#     cursor = memories_collection.find({
#         'chat_sessionId': chat_sessionId,
#         'enabled': True,
#         'embedding': {'$exists': True},
#     })

#     scored = []
#     for doc in cursor:
#         score = cosine_similarity(query_vec, doc['embedding'])
#         scored.append((score, doc))

#     scored.sort(key=lambda x: x[0], reverse=True)

#     return [serialize_memory(d[1]) for d in scored[:limit]]


def search_memories(chat_sessionId: str, query: str, limit: int = 5, threshold: float = 0.5):
    if not query or not query.strip():
        return []

    try:
        query_vec = embed([query])[0]
    except Exception:
        return []

    cursor = memories_collection.find(
        {
            'chat_sessionId': chat_sessionId,
            'enabled': True,
            'embedding': {'$exists': True},
        }
    ).limit(100)  # Limit initial fetch

    scored = []
    for doc in cursor:
        try:
            score = cosine_similarity(query_vec, doc['embedding'])
            if score >= threshold:
                scored.append((score, doc))
        except Exception:
            continue

    scored.sort(key=lambda x: x[0], reverse=True)

    return [serialize_memory(d[1]) for d in scored[:limit]]


async def compress_memories(chat_sessionId: str, model: str):
    memories = list_enabled_memories(chat_sessionId)

    if len(memories) < 2:
        return None

    text = '\n'.join(f'- {m["content"]}' for m in memories)

    prompt = f"""
Summarize the following memories into a concise, structured long-term memory.
Do not lose important facts.
Do not add explanation.

Memories:
{text}
"""

    try:
        summary = await call_ollama_once(prompt, model)
    except Exception:
        return None

    # Disable old memories after successful compression
    for m in memories:
        set_memory_enabled(m['id'], False)

    return add_memory(
        content=summary,
        chat_sessionId=chat_sessionId,
        source='compress',
    )


def should_remember(user_text: str, assistant_text: str) -> bool:
    """Decide if a conversation turn should be saved as memory."""
    if len(assistant_text.strip()) < 30:
        return False

    if len(user_text) + len(assistant_text) < 50:
        return False

    # Check for reject patterns (case-insensitive, whole message)
    reject_patterns = ['dont remember']
    normalized = assistant_text.lower().strip()
    if any(pattern in normalized for pattern in reject_patterns):
        return False

    # Check for explicit remember requests
    accept_patterns = ['remember', 'save this', 'keep in mind']
    if any(pattern in normalized for pattern in accept_patterns):
        return True

    return True


async def summarize(text: str, model: str) -> str:
    prompt = f"""
Summarize the following content into a single concise fact.
Do NOT add explanation.

Content:
{text}
"""
    try:
        return await call_ollama_once(prompt, model)
    except Exception:
        return text[:500]  # Fallback to truncation


async def auto_memory_if_needed(
    chat_sessionId: str,
    user_text: str,
    assistant_text: str,
    model: str,
):
    if not should_remember(user_text, assistant_text):
        print('Auto Memory PASSED')
        return None

    print('Auto Memory TRIGGERED')

    combined = f'User: {user_text}\nAssistant: {assistant_text}'

    summary = await summarize(combined, model)

    try:
        return add_memory(
            content=summary,
            chat_sessionId=chat_sessionId,
            source='auto',
        )
    except Exception as e:
        print(f'Failed to add auto memory: {e}')
        return None
