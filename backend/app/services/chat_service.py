import time
import uuid
from datetime import datetime
from typing import Generator
from urllib.parse import quote

from app.core.db import sessions_collection
from app.services.memory_service import (
    delete_memories_for_session,
    search_memories,
)
from app.services.web_search_service import maybe_extract, maybe_web_search

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


async def build_prompt_with_memory(
    user_content: str,
    chat_sessionId: str = 'default',
) -> str:
    """
    Build final prompt with persistent memories + web search + extracted content.

    Pipeline:
    1. Semantic memory retrieval
    2. URL extraction (explicit > implicit)
    3. Web search (only if NOT explicit extract)
    4. Combine all sources with provenance
    5. Cap prompt length for model safety
    """

    if not user_content or not user_content.strip():
        return ''

    user_content = user_content.strip()
    user_lower = user_content.lower()

    MAX_EXTRACT_CHARS = 3000
    MAX_PROMPT_LENGTH = 12000

    blocks: list[str] = []

    metadata = {
        'memory_count': 0,
        'memory_sources': [],
        'web_count': 0,
        'web_sources': set(),
        'extracted': False,
    }

    # --------------------------------------------------
    # Detect explicit extract intent
    # --------------------------------------------------
    EXTRACT_KEYWORDS = [
        'extract',
        'local extract',
        'tavily extract',
    ]

    is_explicit_extract = any(k in user_lower for k in EXTRACT_KEYWORDS)

    # ==================================================
    # 1. Persistent Memories
    # ==================================================
    try:
        memories = search_memories(chat_sessionId, user_content, limit=10)

        if memories:
            memory_lines = []
            sources = set()

            for m in memories:
                src = m.get('source', 'memory')
                sources.add(src)
                label = f'[{src.upper()}]'
                memory_lines.append(f'  {label} {m["content"]}')

            metadata['memory_count'] = len(memories)
            metadata['memory_sources'] = sorted(sources)

            blocks.append(
                '## PERSISTENT MEMORY\n'
                f'Items: {len(memories)}\n'
                f'Source(s): {", ".join(metadata["memory_sources"])}\n'
                'Relevance: Semantically matched\n\n' + '\n'.join(memory_lines)
            )
    except Exception as e:
        print(f'[build_prompt] Memory search failed: {e}')

    # ==================================================
    # 2. URL Extraction (explicit OR auto)
    # ==================================================
    try:
        extracted = await maybe_extract(user_content)

        if extracted and extracted.strip():
            metadata['extracted'] = True

            preview = extracted[:MAX_EXTRACT_CHARS]
            if len(extracted) > MAX_EXTRACT_CHARS:
                preview += '\n\n[... content truncated ...]'

            blocks.append(
                '## EXTRACTED WEB CONTENT\n'
                'Method: Smart extract (Tavily → Local fallback)\n'
                f'Length: {len(extracted)} chars\n\n' + preview
            )
    except Exception as e:
        print(f'[build_prompt] Web extract failed: {e}')

    # ==================================================
    # 3. Web Search (ONLY if NOT explicit extract)
    # ==================================================
    if not is_explicit_extract and not metadata['extracted']:
        try:
            web_results = await maybe_web_search(user_content, limit=5)

            if web_results:
                web_lines = []

                for r in web_results:
                    source = r.get('source', 'unknown').upper()
                    metadata['web_sources'].add(source)

                    web_lines.append(
                        f'  [{source}] {r.get("title", "")}\n'
                        f'    {r.get("snippet", "")}\n'
                        f'    Link: {r.get("link", "")}'
                    )

                metadata['web_count'] = len(web_results)

                blocks.append(
                    '## WEB SEARCH RESULTS\n'
                    f'Results: {len(web_results)}\n'
                    f'Provider(s): {", ".join(sorted(metadata["web_sources"]))}\n'
                    f'Query: {user_content[:120]}\n\n' + '\n'.join(web_lines)
                )
        except Exception as e:
            print(f'[build_prompt] Web search failed: {e}')
    else:
        print('[build_prompt] Skipping web search (explicit extract detected)')

    # ==================================================
    # 4. Summary Header
    # ==================================================
    summary_header = f"""
=== PROMPT CONTEXT SUMMARY ===
User Query: {user_content[:80]}{'...' if len(user_content) > 80 else ''}
Session: {chat_sessionId}

Sources Used:
 • Memories: {metadata['memory_count']} ({', '.join(metadata['memory_sources']) if metadata['memory_sources'] else 'none'})
 • Web Search: {metadata['web_count']} ({', '.join(sorted(metadata['web_sources'])) if metadata['web_sources'] else 'not used'})
 • Web Extract: {'YES' if metadata['extracted'] else 'NO'}

================================
""".strip()

    context = '\n\n'.join(blocks) if blocks else 'No augmented context available.'

    prompt = f"""{summary_header}

{context}

---

## USER QUERY
{user_content}
"""

    # ==================================================
    # 5. Hard cap prompt length
    # ==================================================
    if len(prompt) > MAX_PROMPT_LENGTH:
        prompt = (
            prompt[:MAX_PROMPT_LENGTH]
            + '\n\n[... prompt truncated to fit model context window ...]'
        )

    print('FINAL PROMPT:\n', prompt)
    print('CONTEXT METADATA:', metadata)

    return prompt
