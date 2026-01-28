import time
import uuid
from datetime import datetime
from typing import Generator
from urllib.parse import quote

from app.core.db import sessions_collection
from app.services.memory_service import (
    delete_memories_for_session,
    search_memories,
    list_enabled_memories,
)
from app.services.web_search_service import maybe_web_search, maybe_extract

MAX_PROMPT_LENGTH = 8000


def create_session(title: str) -> dict:
    now = datetime.utcnow()

    session = {
        'id': str(uuid.uuid4()),
        'title': title,
        'messages': [],
        'created_at': now,
        'updated_at': now,
    }

    sessions_collection.insert_one(session)

    return {
        'id': session['id'],
        'title': session['title'],
        'messages': [],
        'created_at': session['created_at'],
        'updated_at': session['updated_at'],
    }


def get_session(session_id: str) -> dict | None:
    session = sessions_collection.find_one({'id': session_id}, {'_id': 0})
    return session


def list_sessions() -> list[dict]:
    cursor = sessions_collection.find(
        {},
        {
            '_id': 0,
            'id': 1,
            'title': 1,
            'updated_at': 1,
        },
    ).sort('updated_at', -1)

    return list(cursor)


def rename_session(session_id: str, title: str) -> dict:
    result = sessions_collection.update_one(
        {'id': session_id}, {'$set': {'title': title, 'updated_at': datetime.utcnow()}}
    )

    if result.matched_count == 0:
        return None

    return {'id': session_id, 'title': title}


def delete_session(session_id: str) -> bool:
    result = sessions_collection.delete_one({'id': session_id})
    if result.deleted_count != 1:
        return False

    # Also delete any memories tied to this chat session
    delete_memories_for_session(session_id)
    return True


def add_message(session_id: str, role: str, content: str):
    message = {'role': role, 'content': content, 'created_at': datetime.utcnow()}

    result = sessions_collection.update_one(
        {'id': session_id},
        {'$push': {'messages': message}, '$set': {'updated_at': datetime.utcnow()}},
    )

    if result.matched_count == 0:
        raise ValueError('Session not found')

    return message


def stream_chat_reply(session_id: str, content: str) -> Generator[str, None, None]:
    sessions_collection.update_one(
        {'id': session_id},
        {
            '$push': {
                'messages': {'role': 'user', 'content': content, 'created_at': datetime.utcnow()}
            },
            '$set': {'updated_at': datetime.utcnow()},
        },
    )

    reply = f'You said: {content}'

    assistant_msg = ''

    for ch in reply:
        assistant_msg += ch
        yield f'data: {quote(ch)}\n\n'
        time.sleep(0.02)

    sessions_collection.update_one(
        {'id': session_id},
        {
            '$push': {
                'messages': {
                    'role': 'assistant',
                    'content': assistant_msg,
                    'created_at': datetime.utcnow(),
                }
            },
            '$set': {'updated_at': datetime.utcnow()},
        },
    )

    yield 'event: done\ndata: [DONE]\n\n'


async def build_prompt_with_memory(user_content: str, chat_sessionId: str = 'default') -> str:
    """
    Build final prompt with persistent memories + web search + extracted content.

    1. Searches persistent memories (semantic similarity)
    2. Performs web search if needed
    3. Extracts content from URLs
    4. Combines all sources with clear provenance
    5. Caps total length to fit model context
    
    Returns: Full prompt ready for LLM with annotated sources
    """
    if not user_content or not user_content.strip():
        return ""

    blocks = []
    metadata = {
        'memory_count': 0,
        'memory_sources': [],
        'web_count': 0,
        'web_sources': set(),
        'extracted': False,
    }

    # ===== Persistent Memories =====
    try:
        # memories = list_enabled_memories(chat_sessionId)
        memories = search_memories(chat_sessionId, user_content, limit=10)
        if memories:
            memory_lines = []
            for m in memories:
                source_label = f"[{m['source'].upper()}]" if m.get('source') else "[MEMORY]"
                memory_lines.append(f"  {source_label} {m['content']}")
            
            metadata['memory_count'] = len(memories)
            metadata['memory_sources'] = list(set(m.get('source', 'manual') for m in memories))
            
            blocks.append(
                f"## PERSISTENT MEMORY ({len(memories)} items)\n"
                f"Type(s): {', '.join(metadata['memory_sources'])}\n"
                f"Relevance: Semantically matched to user query\n\n"
                + "\n".join(memory_lines)
            )
    except Exception as e:
        print(f"Memory search failed: {e}")

    # ===== Web Search =====
    try:
        web_results = await maybe_web_search(user_content, limit=5)
        if web_results:
            web_lines = []
            for r in web_results:
                source = r.get('source', 'unknown').upper()
                metadata['web_sources'].add(source)
                web_lines.append(
                    f"  [{source}] {r['title']}\n"
                    f"    {r['snippet']}\n"
                    f"    Link: {r['link']}"
                )
            
            metadata['web_count'] = len(web_results)
            
            blocks.append(
                f"## WEB SEARCH RESULTS ({len(web_results)} results)\n"
                f"Provider(s): {', '.join(sorted(metadata['web_sources']))}\n"
                f"Query: {user_content[:100]}\n\n"
                + "\n".join(web_lines)
            )
    except Exception as e:
        print(f"Web search failed: {e}")

    # ===== Web Content Extraction =====
    try:
        extracted = await maybe_extract(user_content)
        if extracted:
            metadata['extracted'] = True
            # Cap extracted content but preserve structure
            extracted_preview = extracted[:3000]
            if len(extracted) > 3000:
                extracted_preview += "\n[... content truncated ...]"
            
            blocks.append(
                f"## EXTRACTED WEB CONTENT\n"
                f"Method: Smart extraction (Tavily → Local fallback)\n"
                f"Length: {len(extracted)} chars\n\n"
                + extracted_preview
            )
    except Exception as e:
        print(f"Web extract failed: {e}")

    # ===== Build Summary Header =====
    summary_header = f""" === PROMPT CONTEXT SUMMARY ===
User Query: {user_content[:80]}{"..." if len(user_content) > 80 else ""}
Session: {chat_sessionId}

 Sources used:
  • Persistent Memories: {metadata['memory_count']} items ({', '.join(metadata['memory_sources']) if metadata['memory_sources'] else 'none'})
  • Web Search: {metadata['web_count']} results ({', '.join(sorted(metadata['web_sources'])) if metadata['web_sources'] else 'not used'})
  • Web Extract: {'Yes' if metadata['extracted'] else 'No'}

================================
"""

    context = "\n".join(blocks)

    prompt = f"""{summary_header}

{context if context else "No augmented context available."}

---

## USER QUERY
{user_content}
"""

    # Cap total prompt length
    if len(prompt) > MAX_PROMPT_LENGTH:
        prompt = prompt[:MAX_PROMPT_LENGTH] + "\n\n[... prompt truncated to fit context window ...]"

    print('FINAL PROMPT:\n', prompt)
    print('CONTEXT METADATA:', metadata)

    return prompt