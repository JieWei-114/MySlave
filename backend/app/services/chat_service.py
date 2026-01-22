import time
import uuid
from datetime import datetime
from typing import Generator
from urllib.parse import quote

from app.core.db import sessions_collection
from app.services.memory_service import (
    delete_memories_for_session,
    list_enabled_memories,
)
from app.services.memory_service import search_memories


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


def build_prompt_with_memory(user_content: str, chat_sessionId: str = 'default') -> str:
    """
    Build final prompt with persistent memories + user input
    """

    # memories = list_enabled_memories(chat_sessionId)
    memories = search_memories(chat_sessionId, user_content, limit=5)

    if not memories:
        return user_content

    memory_block = '\n'.join(f'- {m["content"]}' for m in memories)

    prompt = f"""You are an assistant.

The following are persistent memories about the user.
{memory_block}

Conversation:
User: {user_content}
"""

    print('FINAL PROMPT:\n', prompt)

    return prompt
