"""
Memory Service

Handles storage, retrieval, and management of user memories (facts, preferences, file references).
Uses semantic search with embeddings for intelligent context matching

"""

import logging
import uuid
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId

from app.config.settings import settings
from app.core.db import (
    sessions_collection,
    synthesized_memory_collection,
)
from app.services.embedding_service import cosine_similarity, embed
from app.services.ollama_service import call_ollama_once

logger = logging.getLogger(__name__)

# Import centralized settings
SEARCH_LIMIT = settings.MEMORY_SEARCH_LIMIT
SEARCH_THRESHOLD = settings.MEMORY_SEARCH_THRESHOLD
MAX_CHARS_PER_ITEM = settings.MEMORY_MAX_CHARS_PER_ITEM
MEMORY_DB_QUERY_LIMIT = settings.MEMORY_DB_QUERY_LIMIT
MEMORY_TEXT_FALLBACK_LIMIT = settings.MEMORY_TEXT_FALLBACK_LIMIT
MEMORY_KEY_TRUNCATION_LIMIT = settings.MEMORY_KEY_TRUNCATION_LIMIT
MEMORY_LOG_TRUNCATION_LIMIT = settings.MEMORY_LOG_TRUNCATION_LIMIT


def serialize_memory(doc: dict) -> dict:
    # Convert synthesized memory document to API-friendly format
    return {
        'id': doc.get('id') or str(doc.get('_id')),
        'content': doc.get('value') or doc.get('content') or doc.get('fact') or '',
        'enabled': doc.get('enabled', True),
        'created_at': doc.get('created_at'),
        'chat_sessionId': doc.get('session_id') or doc.get('chat_sessionId'),
        'category': doc.get('category', 'other'),
        'source': doc.get('source', 'manual'),
        'confidence': doc.get('confidence', settings.MEMORY_DEFAULT_CONFIDENCE),
    }


def get_session_memory_limit(session_id: str) -> int | None:
    """
    Get custom memory search limit for a session.

    Sessions can override default memory limit via rules.memorySearchLimit.
    Used to control how many memories are returned in search results.

    """
    try:
        session = sessions_collection.find_one({'id': session_id}, {'rules.memorySearchLimit': 1})
        if session and session.get('rules'):
            return session['rules'].get('memorySearchLimit')
        return None
    except Exception as e:
        logger.error(f'Error fetching memory limit for session {session_id}: {e}')
        return None


def add_memory(
    content: str,
    chat_sessionId: str,
    source: str = 'manual',
    category: str = 'other',
):
    if not content or not content.strip():
        raise ValueError('Content cannot be empty')

    if settings.MEMORY_MAX_CONTENT_LENGTH and len(content) > settings.MEMORY_MAX_CONTENT_LENGTH:
        content = content[: settings.MEMORY_MAX_CONTENT_LENGTH]

    try:
        embedding = embed([content])[0]
    except Exception as e:
        raise ValueError(f'Failed to generate embedding: {e}')

    memory = {
        'id': str(uuid.uuid4()),
        'session_id': chat_sessionId,
        'key': content.strip()[:MEMORY_KEY_TRUNCATION_LIMIT],
        'value': content.strip(),
        'embedding': embedding,
        'source': source,
        'category': category,
        'confidence': settings.MEMORY_DEFAULT_CONFIDENCE,
        'tags': [category],
        'enabled': True,
        'is_deprecated': False,
        'created_at': datetime.utcnow(),
        'last_referenced_at': datetime.utcnow(),
    }
    result = synthesized_memory_collection.insert_one(memory)
    memory['_id'] = result.inserted_id
    return serialize_memory(memory)


def list_all_memories(chat_sessionId: str):
    """
    Get all memories for a session (enabled and disabled).

    Sorted by creation date ascending.
    Used for listing UI to show all stored memories.

    """
    cursor = synthesized_memory_collection.find({'session_id': chat_sessionId}).sort(
        'created_at', 1
    )
    return [serialize_memory(doc) for doc in cursor]


def set_memory_enabled(memory_id: str, enabled: bool):
    """
    Enable or disable a memory without deleting it.

    Disabled memories are not returned in searches or context selection.

    """
    result = synthesized_memory_collection.update_one(
        {'id': memory_id}, {'$set': {'enabled': enabled}}
    )
    if result.matched_count == 0:
        try:
            oid = ObjectId(memory_id)
            result = synthesized_memory_collection.update_one(
                {'_id': oid}, {'$set': {'enabled': enabled}}
            )
        except InvalidId:
            result = None

    if not result or result.matched_count == 0:
        raise ValueError('Invalid memory id')


def list_enabled_memories(chat_sessionId: str):
    """
    Get only enabled memories for a session.

    Excludes disabled memories.
    Used for context selection in chat responses.

    """
    cursor = synthesized_memory_collection.find(
        {
            'session_id': chat_sessionId,
            'is_deprecated': {'$ne': True},
            '$or': [{'enabled': True}, {'enabled': {'$exists': False}}],
        }
    ).sort('created_at', 1)

    return [serialize_memory(doc) for doc in cursor]


def list_memories_by_category(chat_sessionId: str, category: str):
    """
    Get enabled memories for a session filtered by category.

    """
    cursor = synthesized_memory_collection.find(
        {
            'session_id': chat_sessionId,
            'category': category,
            'is_deprecated': {'$ne': True},
            '$or': [{'enabled': True}, {'enabled': {'$exists': False}}],
        }
    ).sort('created_at', 1)

    return [serialize_memory(doc) for doc in cursor]


def delete_memory(memory_id: str):
    """
    Permanently delete a memory item.

    """
    result = synthesized_memory_collection.delete_one({'id': memory_id})
    if result.deleted_count == 0:
        try:
            oid = ObjectId(memory_id)
            result = synthesized_memory_collection.delete_one({'_id': oid})
        except InvalidId:
            raise ValueError('Invalid memory id')


def delete_memories_for_session(chat_sessionId: str) -> int:
    """
    Delete all memories linked to a chat session.

    Called when a session is deleted to clean up associated memories.

    """
    result = synthesized_memory_collection.delete_many({'session_id': chat_sessionId})
    return result.deleted_count


def search_memories(chat_sessionId: str, query: str, limit: int = None, threshold: float = None):
    """
    Search memories using semantic similarity with embeddings.

    Implementation:
    1. Embed the query text using sentence-transformers
    2. Calculate cosine similarity to all memories
    3. Filter by confidence threshold
    4. Return top results sorted by similarity

    """
    if not query or not query.strip():
        return []

    # Use session-specific limit if set, otherwise use settings default
    if limit is None:
        session_limit = get_session_memory_limit(chat_sessionId)
        limit = session_limit or settings.MEMORY_SEARCH_LIMIT

    # Use threshold from settings (can be customized later per session)
    if threshold is None:
        threshold = settings.MEMORY_SEARCH_THRESHOLD

    logger.info(
        'Memory search start (query_len=%s, limit=%s, threshold=%s)',
        len(query),
        limit,
        threshold,
        extra={'session_id': chat_sessionId},
    )

    try:
        query_vec = embed([query])[0]
    except Exception as e:
        logger.error(f'Failed to embed query: {e}')
        return []

    cursor = synthesized_memory_collection.find(
        {
            'session_id': chat_sessionId,
            'is_deprecated': {'$ne': True},
            '$or': [{'enabled': True}, {'enabled': {'$exists': False}}],
            'embedding': {'$exists': True},
        }
    ).limit(MEMORY_DB_QUERY_LIMIT)

    scored = []
    for doc in cursor:
        try:
            score = cosine_similarity(query_vec, doc['embedding'])
            if score >= threshold:
                # Truncate content to max chars per item
                content = doc.get('value') or doc.get('content', '')
                if len(content) > MAX_CHARS_PER_ITEM:
                    if doc.get('value'):
                        doc['value'] = content[:MAX_CHARS_PER_ITEM] + '...'
                    else:
                        doc['content'] = content[:MAX_CHARS_PER_ITEM] + '...'

                scored.append((score, doc))
        except Exception:
            continue

    scored.sort(key=lambda x: x[0], reverse=True)

    results = [serialize_memory(d[1]) for d in scored[:limit]]
    logger.info(
        'Memory search results (matched=%s, returned=%s)',
        len(scored),
        len(results),
        extra={'session_id': chat_sessionId},
    )
    return results


async def compress_memories(chat_sessionId: str, model: str):
    memories = list_enabled_memories(chat_sessionId)

    if len(memories) < 2:
        return None

    text = '\n'.join(f'- {m["content"]}' for m in memories)

    prompt = f"""
Summarize the following memories into a concise.
Structured in long-term memory.
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
        category='other',
    )


def should_remember(user_text: str, assistant_text: str) -> bool:
    # Decide if a conversation turn should be saved as memory
    min_assistant = settings.MEMORY_MIN_ASSISTANT_LENGTH or 0
    min_conversation = settings.MEMORY_MIN_CONVERSATION_LENGTH or 0

    if len(assistant_text.strip()) < min_assistant:
        return False

    if len(user_text) + len(assistant_text) < min_conversation:
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
        return text[:MEMORY_TEXT_FALLBACK_LIMIT]  # Fallback to truncation


async def auto_memory_if_needed(
    chat_sessionId: str,
    user_text: str,
    assistant_text: str,
    model: str,
):
    if not should_remember(user_text, assistant_text):
        logger.debug('Auto memory criteria not met, skipping')
        return None

    logger.info('Auto memory triggered for this conversation')

    combined = f'User: {user_text}\nAssistant: {assistant_text}'

    summary = await summarize(combined, model)

    try:
        return add_memory(
            content=summary,
            chat_sessionId=chat_sessionId,
            source='auto',
            category='preference_or_fact',
        )
    except Exception as e:
        logger.error(f'Failed to add auto memory: {e}')
        return None


# ============================================================
# NEW: SYNTHESIZED MEMORY FUNCTIONS (Facts & Preferences)
# ============================================================


async def add_synthesized_memory(
    session_id: str,
    fact: str,
    category: str = 'general',
    confidence: float = None,
    source: str = 'user_statement',
    tags: list[str] | None = None,
    source_file: str | None = None,
) -> dict:
    """Store a synthesized memory item (fact or preference)"""
    if confidence is None:
        confidence = settings.MEMORY_DEFAULT_CONFIDENCE
    if tags is None:
        tags = []

    embedding = None
    try:
        if fact and fact.strip():
            embedding = embed([fact])[0]
    except Exception as e:
        logger.warning(f'Failed to embed synthesized memory: {e}')

    memory_item = {
        'id': str(uuid.uuid4()),
        'session_id': session_id,
        'category': category,
        'key': fact[:MEMORY_KEY_TRUNCATION_LIMIT],  # Use beginning as key
        'value': fact,
        'confidence': min(1.0, max(0.0, confidence)),  # Clamp 0-1
        'source': source,
        'tags': tags,
        'enabled': True,
        'created_at': datetime.utcnow(),
        'last_referenced_at': datetime.utcnow(),
        'is_deprecated': False,
    }

    if embedding is not None:
        memory_item['embedding'] = embedding

    if source_file:
        memory_item['source_file'] = source_file

    result = synthesized_memory_collection.insert_one(memory_item)
    memory_item['_id'] = result.inserted_id
    logger.info(
        f'Synthesized memory added: {fact[:MEMORY_LOG_TRUNCATION_LIMIT]}... (confidence: {confidence})'
    )
    return memory_item
