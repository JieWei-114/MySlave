from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatSession(BaseModel):
    id: str
    title: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
