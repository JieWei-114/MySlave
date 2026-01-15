import uuid
import time 

from datetime import datetime
from bson import ObjectId
from typing import Generator

from app.core.db import sessions_collection

def create_session(title: str) -> dict:
    now = datetime.utcnow()

    session = {
        "id": str(uuid.uuid4()),
        "title": title,
        "messages": [],
        "created_at": now,
        "updated_at": now
    }

    sessions_collection.insert_one(session) 

    return {
        "id": session["id"],
        "title": session["title"],
        "messages": [],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
    }


def list_sessions() -> list[dict]:
    cursor = sessions_collection.find(
        {},
        {
            "_id": 0,          
            "id": 1,
            "title": 1,
            "updated_at": 1,
        }
    ).sort("updated_at", -1)

    return list(cursor)

def add_message(session_id: str, role: str, content: str):
    message = {
        "role": role,
        "content": content,
        "created_at": datetime.utcnow()
    }

    result = sessions_collection.update_one(
        {"id": session_id},
        {
            "$push": {"messages": message},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    if result.matched_count == 0:
        raise ValueError("Session not found")

    return message

def get_session(session_id: str) -> dict | None:
    session = sessions_collection.find_one(
        {"id": session_id},
        {"_id": 0}
    )
    return session

def delete_session(session_id: str) -> bool:
    result = sessions_collection.delete_one({"id": session_id})
    return result.deleted_count == 1

def stream_chat_reply(
    session_id: str,
    content: str
) -> Generator[str, None, None]:

    # 1️⃣ 先存 user message
    sessions_collection.update_one(
        {"id": session_id},
        {
            "$push": {
                "messages": {
                    "role": "user",
                    "content": content,
                    "created_at": datetime.utcnow()
                }
            },
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    # 2️⃣ mock token stream（之后换 AI）
    reply = f"You said: {content}"

    assistant_msg = ""

    for ch in reply:
        assistant_msg += ch
        yield f"data: {ch}\n\n"
        time.sleep(0.02)

    # 3️⃣ stream 完成后才存 assistant
    sessions_collection.update_one(
        {"id": session_id},
        {
            "$push": {
                "messages": {
                    "role": "assistant",
                    "content": assistant_msg,
                    "created_at": datetime.utcnow()
                }
            },
            "$set": {"updated_at": datetime.utcnow()}
        }
    )

    yield "event: done\ndata: [DONE]\n\n"

def rename_session(session_id: str, title: str) -> dict:
    result = sessions_collection.update_one(
        {"id": session_id},
        {
            "$set": {
                "title": title,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.matched_count == 0:
        return None

    return {
        "id": session_id,
        "title": title
    }