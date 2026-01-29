from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SessionRules(BaseModel):
    searxng: bool = True
    duckduckgo: bool = True
    tavily: bool = True
    serper: bool = True
    tavilyExtract: bool = True
    localExtract: bool = True


class ChatSession(BaseModel):
    id: str
    title: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    rules: SessionRules = Field(default_factory=SessionRules)
