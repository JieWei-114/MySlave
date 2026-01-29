from typing import List

from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    title: str


class SendMessageRequest(BaseModel):
    content: str


class RenameSessionRequest(BaseModel):
    title: str


class CreateMemoryRequest(BaseModel):
    content: str
    chat_sessionId: str


class RulesConfig(BaseModel):
    searxng: bool = True
    duckduckgo: bool = True
    tavily: bool = True
    serper: bool = True
    tavilyExtract: bool = True
    localExtract: bool = True


class ReorderSessionsRequest(BaseModel):
    sessionIds: List[str]
